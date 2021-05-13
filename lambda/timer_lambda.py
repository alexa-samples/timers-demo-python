# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/samples for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import typing
import json
import uuid

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractRequestInterceptor, AbstractExceptionHandler)
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.skill_builder import SkillBuilder, CustomSkillBuilder

from ask_sdk_model.ui import SimpleCard, AskForPermissionsConsentCard
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor
from ask_sdk_model.services.service_exception import ServiceException
from ask_sdk_model.interfaces.connections import SendRequestDirective
from ask_sdk_model.interfaces.tasks import CompleteTaskDirective

from ask_sdk_model.status import Status

if typing.TYPE_CHECKING:
    from ask_sdk_core.handler_input import HandlerInput
    from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

new_timer_request = {
  "duration": "PT10M",
  "timerLabel": "exercise",
  "creationBehavior": {
     "displayExperience": {
         "visibility": "VISIBLE"
    }
 },
  "triggeringBehavior": {
    "operation": {
      "type": "ANNOUNCE",
      "textToAnnounce": [
        {
          "locale": "en-US",
          "text": "That's enough stretching, start to run"
        }
      ]
    },
    "notificationConfig": {
      "playAudible": True
    }
  }
}
 
REQUIRED_PERMISSIONS = ["alexa::alerts:timers:skill:readwrite"]

def get_uuid():
    return str(uuid.uuid4())

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Welcome to timer custom task skill. Please say set timer.").ask("Please say set timer").response


class TimerIntentHandler(AbstractRequestHandler):
    #only can be called if there if timer hasn't been paused
    def can_handle(self, handler_input):
        return is_request_type("IntentRequest")(handler_input) and \
            (is_intent_name("TimerIntent")(handler_input) or 
                is_intent_name("AMAZON.YesIntent")(handler_input))
    
    def handle(self, handler_input):
        logger.info("In TimerIntent Handler")

        response_builder = handler_input.response_builder
        permissions = handler_input.request_envelope.context.system.user.permissions
        if not (permissions and permissions.consent_token):
            return response_builder.add_directive(
                SendRequestDirective(
                    name="AskFor",
                    payload= {
                        "@type": "AskForPermissionsConsentRequest",
                        "@version": "1",
                        "permissionScope": "alexa::alerts:timers:skill:readwrite"
                    },
                    token= "correlationToken"
                )
            ).response
        logger.info("Voice permission provided")
        timer_service = handler_input.service_client_factory.get_timer_management_service()
        timer_response = timer_service.create_timer(new_timer_request)
        logger.info("Timer created")
        
        if str(timer_response.status) == "Status.ON":
            session_attr = handler_input.attributes_manager.session_attributes
            if not session_attr:
                session_attr['lastTimerId'] = timer_response.id

            speech_text = 'Your 10 minutes timer has started!.'
        else:
            speech_text = 'Timer did not start'

        return (
            handler_input.response_builder
            .speak(speech_text)
            .response
        )

class AcceptGrantResponseHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("Alexa.Authorization.Grant")(handler_input)

    def handle(self, handler_input):
        Get_Accept_Grant_Response = {
            "event": {
                "header": {
                    "namespace": "Alexa.Authorization",
                    "name": "AcceptGrant.Response",
                    "messageId": get_uuid(),
                    "payloadVersion": "3"
                },
                "payload": {}
            }
        }
        print("AcceptGrant Response: ", json.dumps(Get_Accept_Grant_Response))
        return json.loads(json.dumps(Get_Accept_Grant_Response))

class ConnectionsResponsehandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ((is_request_type("Connections.Response")(handler_input) and \
            handler_input.request_envelope.request.name == "AskFor"))

    def handle(self, handler_input):
        logger.info("In Connections Response Handler")

        response_payload = handler_input.request_envelope.request.payload
        response_status = response_payload['status']

        if (response_status == 'NOT_ANSWERED'):
            return handler_input.response_builder.speak("Please provide timer permissions using card I have sent to your Alexa app.").set_card(AskForPermissionsConsentCard(permissions=REQUIRED_PERMISSIONS)).response

        elif (response_status == 'DENIED'):
            return handler_input.response_builder.speak("You can grant permission anytime by going to Alexa app.").response

        else:
            return handler_input.response_builder.speak("Please say set timer").ask("Please say set timer").response

class SessionResumedHandlerRequest(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionResumedRequest")(handler_input)
    
    def handle(self, handler_input):

        response_builder = handler_input.response_builder
        status = handler_input.request_envelope.request.cause.status
        result = handler_input.request_envelope.request.cause.result
        code = status.code
        message = status.message
        speechText = "Got back ! Status code is {}, message is {}".format(code , message)
        if(code == '200'):
            speechText = "Got back ! Status code is {}, message is {} and payload is {}".format(code, message, result.payload)
        
        response_builder.speak(speechText)
        return response_builder.response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return (
            handler_input.response_builder
            .speak("Thank You to using this skill.")
            .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        return (
            handler_input.response_builder
            .speak("To use this skill say set a reminder which will set a reminder for next 5 minutes.")
            .ask("What do you want to ask?")
            .response
        )

class LoggingRequestInterceptor(AbstractRequestInterceptor):
    def process(self, handler_input):
        logger.info("Request Received: {}".format(handler_input.request_envelope))

class LoggingResponseInterceptor(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        logger.info("Response generated: {}".format(response))

class IntentReflectorHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = 'You just triggered {}'.format(intent_name)

        return (
            handler_input.response_builder
            .speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open for the user to respond")
            .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        
        return (
            handler_input.response_builder
            .speak("Uh Oh. Looks like something went wrong.")
            .ask("Uh Oh. Looks like something went wrong.")
            .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

sb = CustomSkillBuilder(api_client=DefaultApiClient())

sb.add_request_handler(LaunchRequestHandler())

sb.add_request_handler(TimerIntentHandler())
sb.add_request_handler(AcceptGrantResponseHandler())
sb.add_request_handler(ConnectionsResponsehandler())
sb.add_request_handler(SessionResumedHandlerRequest())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Adding Request and Response interceptor
sb.add_global_request_interceptor(LoggingRequestInterceptor())
sb.add_global_response_interceptor(LoggingResponseInterceptor())

handler = sb.lambda_handler()
