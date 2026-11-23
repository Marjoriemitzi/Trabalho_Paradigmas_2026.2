module Main exposing (main)

import Api
import Browser
import Html exposing (Html, button, div, form, h1, input, label, p, text)
import Html.Attributes exposing (attribute, disabled, for, id, minlength, required, type_, value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Json.Decode as Decode
import Json.Encode as Encode


type alias User =
    { id : String
    , email : String
    }


type alias Model =
    { email : String
    , password : String
    , confirmation : String
    , registering : Bool
    , loading : Bool
    , error : String
    , notice : String
    , user : Maybe User
    }


type Msg
    = ChangeEmail String
    | ChangePassword String
    | ChangeConfirmation String
    | ToggleRegister
    | Submit
    | ReceiveResponse Api.Response
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
    , user = Nothing
    }


main : Program Bool Model Msg
main =
    Browser.element
        { init = init
        , update = update
        , view = view
        , subscriptions = \_ -> Api.responses ReceiveResponse
        }


init : Bool -> ( Model, Cmd Msg )
init restoring =
    ( { initialModel | loading = restoring }, Cmd.none )


userDecoder : Decode.Decoder User
userDecoder =
    Decode.map2 User
        (Decode.field "id" Decode.string)
        (Decode.field "email" Decode.string)


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

        ReceiveResponse response ->
            receiveResponse response model

        Logout ->
            ( initialModel, Api.logout )


receiveResponse : Api.Response -> Model -> ( Model, Cmd Msg )
receiveResponse response model =
    case response.id of
        "login" ->
            if response.status == 200 && response.error == Nothing then
                ( { model | password = "" }
                , Api.request
                    { id = "profile"
                    , method = "GET"
                    , path = "/users/me"
                    , body = Encode.null
                    }
                )

            else
                ( { model | loading = False, error = requestError False response }, Cmd.none )

        "registration" ->
            if response.status == 201 then
                ( { initialModel
                    | email = model.email
                    , notice = "Conta criada com sucesso. Entre para continuar."
                  }
                , Cmd.none
                )

            else
                ( { model | loading = False, error = requestError True response }, Cmd.none )

        "profile" ->
            case Decode.decodeValue userDecoder response.body of
                Ok user ->
                    if response.status == 200 then
                        ( { initialModel | user = Just user }, Cmd.none )

                    else
                        ( profileError model response, Cmd.none )

                Err _ ->
                    ( profileError model response, Cmd.none )

        "session-ended" ->
            ( profileError model response, Cmd.none )

        _ ->
            ( model, Cmd.none )


profileError : Model -> Api.Response -> Model
profileError model response =
    { initialModel
        | email = model.email
        , error =
            if response.status == 401 then
                "Sua sessão expirou ou não é válida. Entre novamente."

            else
                "Não foi possível consultar sua conta. Tente entrar novamente."
    }


submitCredentials : Model -> Cmd Msg
submitCredentials model =
    let
        body =
            Encode.object
                [ ( "email", Encode.string (String.trim model.email) )
                , ( "password", Encode.string model.password )
                ]
    in
    if model.registering then
        Api.register body

    else
        Api.login body


requestError : Bool -> Api.Response -> String
requestError registering response =
    case response.status of
        401 ->
            "E-mail ou senha incorretos."

        409 ->
            "Este e-mail já está cadastrado. Entre na sua conta."

        422 ->
            if registering then
                "Confira o e-mail e os requisitos da senha."

            else
                "Confira o e-mail e a senha informados."

        429 ->
            case response.retryAfter of
                Just seconds ->
                    "Muitas tentativas. Aguarde " ++ String.fromInt seconds ++ " segundos antes de tentar novamente."

                Nothing ->
                    "Muitas tentativas. Aguarde antes de tentar novamente."

        _ ->
            case response.error of
                Just "network_error" ->
                    "Não foi possível conectar ao servidor."

                Just "timeout" ->
                    "O servidor demorou para responder. Tente novamente."

                _ ->
                    "Não foi possível concluir a operação. Tente novamente."


view : Model -> Html Msg
view model =
    div []
        [ h1 [] [ text "Finanças pessoais" ]
        , case model.user of
            Just user ->
                div []
                    [ p [] [ text "Bem-vindo!" ]
                    , p [] [ text user.email ]
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
