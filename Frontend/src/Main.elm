module Main exposing (main)

import Browser
import Html exposing (Html, button, div, form, h1, input, label, p, text)
import Html.Attributes exposing (autocomplete, disabled, for, id, required, type_, value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode as Decode
import Json.Encode as Encode


type alias Model =
    { email : String
    , password : String
    , loading : Bool
    , error : String
    , token : Maybe String
    }


type Msg
    = ChangeEmail String
    | ChangePassword String
    | SubmitLogin
    | ReceiveLogin (Result Http.Error String)
    | Logout


initialModel : Model
initialModel =
    { email = ""
    , password = ""
    , loading = False
    , error = ""
    , token = Nothing
    }


main : Program () Model Msg
main =
    Browser.element
        { init = \_ -> ( initialModel, Cmd.none )
        , update = update
        , view = view
        , subscriptions = \_ -> Sub.none
        }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ChangeEmail email ->
            ( { model | email = email, error = "" }, Cmd.none )

        ChangePassword password ->
            ( { model | password = password, error = "" }, Cmd.none )

        SubmitLogin ->
            if model.loading then
                ( model, Cmd.none )

            else
                ( { model | loading = True, error = "" }
                , login model.email model.password
                )

        ReceiveLogin result ->
            case result of
                Ok token ->
                    ( { model
                        | token = Just token
                        , password = ""
                        , loading = False
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model | error = loginError error, loading = False }
                    , Cmd.none
                    )

        Logout ->
            ( initialModel, Cmd.none )


login : String -> String -> Cmd Msg
login email password =
    Http.request
        { method = "POST"
        , headers = []
        , url = "/api/v1/auth/login"
        , body =
            Http.jsonBody
                (Encode.object
                    [ ( "email", Encode.string (String.trim email) )
                    , ( "password", Encode.string password )
                    ]
                )
        , expect =
            Http.expectJson ReceiveLogin
                (Decode.field "access_token" Decode.string)
        , timeout = Just 15000
        , tracker = Nothing
        }


loginError : Http.Error -> String
loginError error =
    case error of
        Http.BadStatus 401 ->
            "E-mail ou senha incorretos."

        Http.BadStatus 422 ->
            "Confira o e-mail e a senha informados."

        Http.NetworkError ->
            "Não foi possível conectar ao servidor."

        Http.Timeout ->
            "O servidor demorou para responder. Tente novamente."

        _ ->
            "Não foi possível entrar. Tente novamente."


view : Model -> Html Msg
view model =
    div []
        [ h1 [] [ text "Finanças pessoais" ]
        , case model.token of
            Just _ ->
                div []
                    [ p [] [ text "Login realizado com sucesso." ]
                    , button [ onClick Logout ] [ text "Sair" ]
                    ]

            Nothing ->
                form [ onSubmit SubmitLogin ]
                    [ label [ for "email" ] [ text "E-mail" ]
                    , input
                        [ id "email"
                        , type_ "email"
                        , value model.email
                        , onInput ChangeEmail
                        , required True
                        , autocomplete True
                        , disabled model.loading
                        ]
                        []
                    , label [ for "password" ] [ text "Senha" ]
                    , input
                        [ id "password"
                        , type_ "password"
                        , value model.password
                        , onInput ChangePassword
                        , required True
                        , disabled model.loading
                        ]
                        []
                    , p [ Html.Attributes.attribute "role" "alert" ]
                        [ text model.error ]
                    , button
                        [ type_ "submit"
                        , disabled model.loading
                        ]
                        [ text
                            (if model.loading then
                                "Entrando..."

                             else
                                "Entrar"
                            )
                        ]
                    ]
        ]