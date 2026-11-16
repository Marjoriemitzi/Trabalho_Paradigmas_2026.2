module Main exposing (main)

import Browser
import Html exposing (Html, button, div, form, h1, input, label, p, text)
import Html.Attributes exposing (attribute, disabled, for, id, minlength, required, type_, value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Http
import Json.Decode as Decode
import Json.Encode as Encode


type alias Model =
    { email : String
    , password : String
    , confirmation : String
    , registering : Bool
    , loading : Bool
    , error : String
    , notice : String
    , token : Maybe String
    }


type Msg
    = ChangeEmail String
    | ChangePassword String
    | ChangeConfirmation String
    | ToggleRegister
    | Submit
    | ReceiveLogin (Result Http.Error String)
    | ReceiveRegistration (Result Http.Error ())
    | Logout


initialModel : Model
initialModel =
    { email = ""
    , password = ""
    , confirmation = ""
    , registering = False
    , loading = False
    , error = ""
    , notice = ""
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

        ChangeConfirmation confirmation ->
            ( { model | confirmation = confirmation, error = "" }
            , Cmd.none
            )

        ToggleRegister ->
            ( { model
                | registering = not model.registering
                , password = ""
                , confirmation = ""
                , error = ""
                , notice = ""
              }
            , Cmd.none
            )

        Submit ->
            if model.loading then
                ( model, Cmd.none )

            else if model.registering && model.password /= model.confirmation then
                ( { model | error = "As senhas não coincidem." }
                , Cmd.none
                )

            else
                ( { model | loading = True, error = "", notice = "" }
                , submitCredentials model
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
                    ( { model
                        | error = requestError False error
                        , loading = False
                      }
                    , Cmd.none
                    )

        ReceiveRegistration result ->
            case result of
                Ok _ ->
                    ( { initialModel
                        | email = model.email
                        , notice = "Conta criada com sucesso. Entre para continuar."
                      }
                    , Cmd.none
                    )

                Err error ->
                    ( { model
                        | error = requestError True error
                        , loading = False
                      }
                    , Cmd.none
                    )

        Logout ->
            ( initialModel, Cmd.none )


submitCredentials : Model -> Cmd Msg
submitCredentials model =
    Http.request
        { method = "POST"
        , headers = []
        , url =
            if model.registering then
                "/api/v1/users"

            else
                "/api/v1/auth/login"
        , body =
            Http.jsonBody
                (Encode.object
                    [ ( "email", Encode.string (String.trim model.email) )
                    , ( "password", Encode.string model.password )
                    ]
                )
        , expect =
            if model.registering then
                Http.expectJson ReceiveRegistration (Decode.succeed ())

            else
                Http.expectJson ReceiveLogin
                    (Decode.field "access_token" Decode.string)
        , timeout = Just 15000
        , tracker = Nothing
        }


requestError : Bool -> Http.Error -> String
requestError registering error =
    case error of
        Http.BadStatus 401 ->
            "E-mail ou senha incorretos."

        Http.BadStatus 409 ->
            "Este e-mail já está cadastrado. Entre na sua conta."

        Http.BadStatus 422 ->
            if registering then
                "Confira o e-mail e os requisitos da senha."

            else
                "Confira o e-mail e a senha informados."

        Http.NetworkError ->
            "Não foi possível conectar ao servidor."

        Http.Timeout ->
            "O servidor demorou para responder. Tente novamente."

        _ ->
            "Não foi possível concluir a operação. Tente novamente."


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
                credentialsForm model
        ]


credentialsForm : Model -> Html Msg
credentialsForm model =
    let
        passwordAutocomplete =
            if model.registering then
                "new-password"

            else
                "current-password"
    in
    form [ onSubmit Submit ]
        [ p []
            [ text
                (if model.registering then
                    "Crie sua conta"

                 else
                    "Entre na sua conta"
                )
            ]
        , p [ attribute "role" "status" ] [ text model.notice ]
        , field model
            "email"
            "E-mail"
            "email"
            "email"
            model.email
            ChangeEmail
        , field model
            "password"
            "Senha"
            "password"
            passwordAutocomplete
            model.password
            ChangePassword
        , if model.registering then
            div []
                [ p []
                    [ text "Use pelo menos 12 caracteres, incluindo maiúscula, minúscula, número e símbolo." ]
                , field model
                    "confirmation"
                    "Confirme sua senha"
                    "password"
                    "new-password"
                    model.confirmation
                    ChangeConfirmation
                ]

          else
            text ""
        , p [ attribute "role" "alert" ] [ text model.error ]
        , button
            [ type_ "submit", disabled model.loading ]
            [ text
                (if model.loading then
                    "Aguarde..."

                 else if model.registering then
                    "Criar conta"

                 else
                    "Entrar"
                )
            ]
        , p []
            [ button
                [ type_ "button"
                , onClick ToggleRegister
                , disabled model.loading
                ]
                [ text
                    (if model.registering then
                        "Já tenho uma conta"

                     else
                        "Quero me cadastrar"
                    )
                ]
            ]
        ]


field : Model -> String -> String -> String -> String -> String -> (String -> Msg) -> Html Msg
field model fieldId title inputType autocompleteValue current toMsg =
    div []
        [ label [ for fieldId ] [ text title ]
        , input
            [ id fieldId
            , type_ inputType
            , value current
            , onInput toMsg
            , required True
            , disabled model.loading
            , attribute "autocomplete" autocompleteValue
            , minlength
                (if model.registering && inputType == "password" then
                    12

                 else
                    1
                )
            ]
            []
        ]
