# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK.
import logging

from ask_sdk_model.services import ApiConfiguration
from ask_sdk_s3.adapter import S3Adapter
s3_adapter = S3Adapter(bucket_name="aws-codestar-us-west-2-051805255583")

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.serialize import DefaultSerializer
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.services.service_client_factory import ServiceClientFactory
import ask_sdk_model.services.timer_management as timer

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Welcome to Classroom Timer! I can start a timer, do this, or that. Which would you like me to do?"
        reprompt_text = "There are several things I can do. I can start a timer, do this, or that. Which would you like me to do?"
        handler_input.response_builder.speak(speech_text).ask(reprompt_text)
        return handler_input.response_builder.response


class CapturePreferencesIntentHandler(AbstractRequestHandler):
    """Handler for Capture Preferences Intent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("CapturePreferencesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        activity = slots["activity"].value

        attributes_manager = handler_input.attributes_manager
        attributes_manager.persistent_attributes = {
            "activity": activity
        }
        attributes_manager.save_persistent_attributes()

        speak_output = f"Great. I've set your preference for break activity to {activity}. If you want to change it later you can say set break preference."
        return handler_input.response_builder.speak(speak_output).response


class StartTimerHandler(AbstractRequestHandler):
    """Handler for Start Timer Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        attr = handler_input.attributes_manager.persistent_attributes
        return is_intent_name("StartTimerIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        slots = handler_input.request_envelope.request.intent.slots
        duration = int(slots["time"].value)
        speech_text = f"Got it. Starting your timer for {duration} seconds."

        try:
            sys_object = handler_input.request_envelope.context.system
            clientFactory = ServiceClientFactory(ApiConfiguration(
                authorization_value=sys_object.api_access_token,
                api_endpoint=sys_object.api_endpoint,
                serializer=DefaultSerializer(),
                api_client=DefaultApiClient()
            ))
            timerClient = clientFactory.get_timer_management_service()
            timerClient.create_timer(timer.timer_request.TimerRequest(
                duration=f"PT{duration}S",
                timer_label="independent",
                triggering_behavior=timer.triggering_behavior.TriggeringBehavior(
                    timer.notify_only_operation.NotifyOnlyOperation(),
                    timer.notification_config.NotificationConfig(True)
                )
            ))
        except Exception:
            handler_input.response_builder.speak("There was a problem connecting to the service")
            return handler_input.response_builder.response

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "You can say hello to me! How can I help?"
        handler_input.response_builder.speak(speech_text).ask(speech_text)
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Goodbye!"
        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


# The intent reflector is used for interaction model testing and debugging.
# It will simply repeat the intent the user said. You can create custom handlers
# for your intents by defining them above, then also adding them to the request
# handler chain below.
class IntentReflectorHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = handler_input.request_envelope.request.intent.name
        speech_text = ("You just triggered {}").format(intent_name)
        handler_input.response_builder.speak(speech_text).set_should_end_session(True)
        return handler_input.response_builder.response


# Generic error handling to capture any syntax or routing errors. If you receive an error
# stating the request handler chain is not found, you have not implemented a handler for
# the intent being invoked or included it in the skill builder below.
class ErrorHandler(AbstractExceptionHandler):
    """Catch-all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        speech_text = "Sorry, I couldn't understand what you said. Please try again."
        handler_input.response_builder.speak(speech_text).ask(speech_text)
        return handler_input.response_builder.response


# This handler acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.
sb = CustomSkillBuilder(persistence_adapter=s3_adapter)
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CapturePreferencesIntentHandler())
sb.add_request_handler(StartTimerHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(ErrorHandler())

handler = sb.lambda_handler()
