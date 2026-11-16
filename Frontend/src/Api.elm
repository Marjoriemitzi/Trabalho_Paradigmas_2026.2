module Api exposing (Error(..), LoginToken, Profile, login, me, register)

import Http
import Json.Decode as D
import Json.Encode as E


type Error
    = Network
    | Timeout
    | InvalidResponse
    | Rejected Int String (List String) (List String)


type alias LoginToken =
    { accessToken : String, expiresIn : Int }


type alias Profile =
    { id : String, email : String, role : String }


profileDecoder : D.Decoder Profile
profileDecoder =
    D.map3 Profile (D.field "id" D.string) (D.field "email" D.string) (D.field "role" D.string)


expect : D.Decoder a -> (Result Error a -> msg) -> Http.Expect msg
expect decoder toMsg =
    Http.expectStringResponse toMsg
        (\response ->
            case response of
                Http.BadUrl_ _ ->
                    Err InvalidResponse

                Http.Timeout_ ->
                    Err Timeout

                Http.NetworkError_ ->
                    Err Network

                Http.BadStatus_ metadata body ->
                    let
                        errorDecoder =
                            D.map3 (Rejected metadata.statusCode)
                                (D.field "error" D.string)
                                (D.oneOf [ D.field "reasons" (D.list D.string), D.succeed [] ])
                                (D.oneOf
                                    [ D.field "fields" (D.list (D.field "field" (D.nullable D.string)))
                                        |> D.map (List.filterMap identity)
                                    , D.succeed []
                                    ]
                                )
                    in
                    Err (Result.withDefault (Rejected metadata.statusCode "" [] []) (D.decodeString errorDecoder body))

                Http.GoodStatus_ _ body ->
                    D.decodeString decoder body |> Result.mapError (always InvalidResponse)
        )


credentials : String -> String -> Http.Body
credentials email password =
    Http.jsonBody (E.object [ ( "email", E.string email ), ( "password", E.string password ) ])


login : String -> String -> (Result Error LoginToken -> msg) -> Cmd msg
login email password toMsg =
    Http.request
        { method = "POST"
        , headers = []
        , url = "/api/v1/auth/login"
        , body = credentials email password
        , expect = expect (D.map2 LoginToken (D.field "access_token" D.string) (D.field "expires_in" D.int)) toMsg
        , timeout = Just 15000
        , tracker = Nothing
        }


register : String -> String -> (Result Error Profile -> msg) -> Cmd msg
register email password toMsg =
    Http.request
        { method = "POST"
        , headers = []
        , url = "/api/v1/users"
        , body = credentials email password
        , expect = expect profileDecoder toMsg
        , timeout = Just 15000
        , tracker = Nothing
        }


me : String -> (Result Error Profile -> msg) -> Cmd msg
me token toMsg =
    Http.request
        { method = "GET"
        , headers = [ Http.header "Authorization" ("Bearer " ++ token) ]
        , url = "/api/v1/users/me"
        , body = Http.emptyBody
        , expect = expect profileDecoder toMsg
        , timeout = Just 15000
        , tracker = Nothing
        }
