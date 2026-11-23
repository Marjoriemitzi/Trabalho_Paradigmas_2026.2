port module Api exposing (Request, Response, login, logout, register, request, responses)

import Json.Encode as Encode


type alias Request =
    { id : String
    , method : String
    , path : String
    , body : Encode.Value
    }


type alias Response =
    { id : String
    , status : Int
    , error : Maybe String
    , retryAfter : Maybe Int
    , body : Encode.Value
    }


port sendRequest : Request -> Cmd msg


port sendLogin : Encode.Value -> Cmd msg


port sendRegistration : Encode.Value -> Cmd msg


port sendLogout : () -> Cmd msg


port receiveResponse : (Response -> msg) -> Sub msg


login : Encode.Value -> Cmd msg
login =
    sendLogin


register : Encode.Value -> Cmd msg
register =
    sendRegistration


logout : Cmd msg
logout =
    sendLogout ()


request : Request -> Cmd msg
request =
    sendRequest


responses : (Response -> msg) -> Sub msg
responses =
    receiveResponse
