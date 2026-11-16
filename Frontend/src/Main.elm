port module Main exposing (main)

import Api
import Browser
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (onClick, onInput, onSubmit)
import Json.Encode as E
import Time
import Validation


port saveSession : E.Value -> Cmd msg


port clearSession : () -> Cmd msg


port focusField : String -> Cmd msg


type alias Token =
    { value : String, expiresAt : Int }


type alias Flags =
    { now : Int, session : Maybe Token }


type Auth
    = SignedOut
    | Checking Token
    | SignedIn Token Api.Profile
    | SessionProblem Token String


type Page
    = Login
    | Register


type alias Model =
    { page : Page
    , email : String
    , password : String
    , confirmation : String
    , showPassword : Bool
    , submitted : Bool
    , busy : Bool
    , notice : String
    , error : String
    , serverFields : List String
    , auth : Auth
    , attempt : Int
    , now : Int
    }


type Msg
    = ChangePage Page
    | EmailChanged String
    | PasswordChanged String
    | ConfirmationChanged String
    | TogglePassword
    | Submit
    | LoginReceived Int (Result Api.Error Api.LoginToken)
    | RegisterReceived Int (Result Api.Error Api.Profile)
    | ProfileReceived Int (Result Api.Error Api.Profile)
    | Tick Time.Posix
    | Logout
    | RetryProfile


main : Program Flags Model Msg
main =
    Browser.element { init = init, update = update, subscriptions = always (Time.every 1000 Tick), view = view }


init : Flags -> ( Model, Cmd Msg )
init flags =
    let
        model =
            { page = Login, email = "", password = "", confirmation = "", showPassword = False, submitted = False, busy = False, notice = "", error = "", serverFields = [], auth = SignedOut, attempt = 0, now = flags.now }
    in
    case flags.session of
        Just token ->
            if token.expiresAt > flags.now then
                ( { model | auth = Checking token }, Api.me token.value (ProfileReceived 0) )

            else
                ( { model | notice = "Sua sessão expirou. Entre novamente." }, clearSession () )

        Nothing ->
            ( model, Cmd.none )


isRegister : Model -> Bool
isRegister model =
    model.page == Register


validationErrors : Model -> List ( String, String )
validationErrors model =
    Validation.problems (isRegister model) model.email model.password model.confirmation


reset : Model -> Model
reset model =
    { model | password = "", confirmation = "", showPassword = False, submitted = False, busy = False, error = "", serverFields = [], notice = "", attempt = model.attempt + 1 }


signOut : String -> Model -> ( Model, Cmd Msg )
signOut notice model =
    let
        clean =
            reset model
    in
    ( { clean | auth = SignedOut, page = Login, notice = notice }, Cmd.batch [ clearSession (), focusField "email" ] )


tokenOf : Auth -> Maybe Token
tokenOf auth =
    case auth of
        SignedOut ->
            Nothing

        Checking token ->
            Just token

        SignedIn token _ ->
            Just token

        SessionProblem token _ ->
            Just token


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ChangePage page ->
            let
                clean =
                    reset model
            in
            ( { clean | page = page }, focusField "email" )

        EmailChanged email ->
            ( { model | email = email, error = "", serverFields = [] }, Cmd.none )

        PasswordChanged password ->
            ( { model | password = password, error = "", serverFields = [] }, Cmd.none )

        ConfirmationChanged confirmation ->
            ( { model | confirmation = confirmation, error = "", serverFields = [] }, Cmd.none )

        TogglePassword ->
            ( { model | showPassword = not model.showPassword }, Cmd.none )

        Submit ->
            if model.busy then
                ( model, Cmd.none )

            else
                case validationErrors model of
                    ( firstField, _ ) :: _ ->
                        ( { model | submitted = True, notice = "", error = "" }, focusField firstField )

                    [] ->
                        let
                            attempt =
                                model.attempt + 1

                            email =
                                String.toLower (String.trim model.email)

                            command =
                                if isRegister model then
                                    Api.register email model.password (RegisterReceived attempt)

                                else
                                    Api.login email model.password (LoginReceived attempt)
                        in
                        ( { model | email = email, busy = True, submitted = True, error = "", notice = "", serverFields = [], attempt = attempt }, command )

        LoginReceived attempt result ->
            if attempt /= model.attempt then
                ( model, Cmd.none )

            else
                case result of
                    Ok response ->
                        let
                            token =
                                { value = response.accessToken, expiresAt = model.now + response.expiresIn * 1000 }
                        in
                        ( { model | auth = Checking token, password = "", confirmation = "", busy = False, submitted = False, showPassword = False }, Api.me token.value (ProfileReceived attempt) )

                    Err error ->
                        handleError error model

        RegisterReceived attempt result ->
            if attempt /= model.attempt then
                ( model, Cmd.none )

            else
                case result of
                    Ok _ ->
                        let
                            clean =
                                reset model
                        in
                        ( { clean | page = Login, notice = "Conta criada com sucesso. Entre com seu e-mail e senha." }, focusField "password" )

                    Err error ->
                        handleError error model

        ProfileReceived attempt result ->
            if attempt /= model.attempt then
                ( model, Cmd.none )

            else
                case ( tokenOf model.auth, result ) of
                    ( Just token, Ok profile ) ->
                        if token.expiresAt <= model.now then
                            signOut "Sua sessão expirou. Entre novamente." model

                        else
                            ( { model | auth = SignedIn token profile, busy = False, error = "" }
                            , saveSession (E.object [ ( "value", E.string token.value ), ( "expiresAt", E.int token.expiresAt ) ])
                            )

                    ( Just _, Err (Api.Rejected 401 _ _ _) ) ->
                        signOut "Sua sessão expirou ou não é mais válida. Entre novamente." model

                    ( Just _, Err (Api.Rejected 404 _ _ _) ) ->
                        signOut "O usuário desta sessão não está disponível. Entre novamente." model

                    ( Just token, Err error ) ->
                        ( { model | auth = SessionProblem token (errorMessage error) }, Cmd.none )

                    _ ->
                        ( model, Cmd.none )

        Tick now ->
            let
                updated =
                    { model | now = Time.posixToMillis now }
            in
            case tokenOf model.auth of
                Just token ->
                    if token.expiresAt <= updated.now then
                        signOut "Sua sessão expirou. Entre novamente." updated

                    else
                        ( updated, Cmd.none )

                Nothing ->
                    ( updated, Cmd.none )

        Logout ->
            signOut "Você saiu da sua conta." model

        RetryProfile ->
            case tokenOf model.auth of
                Just token ->
                    ( { model | auth = Checking token }, Api.me token.value (ProfileReceived model.attempt) )

                Nothing ->
                    ( model, Cmd.none )


handleError : Api.Error -> Model -> ( Model, Cmd Msg )
handleError error model =
    let
        fields =
            case error of
                Api.Rejected _ "email_taken" _ _ ->
                    [ "email" ]

                Api.Rejected _ "invalid_email" _ _ ->
                    [ "email" ]

                Api.Rejected _ "weak_password" _ _ ->
                    [ "password" ]

                Api.Rejected _ _ _ names ->
                    names

                _ ->
                    []
    in
    ( { model | busy = False, error = errorMessage error, serverFields = fields }
    , List.head fields |> Maybe.map focusField |> Maybe.withDefault Cmd.none
    )


errorMessage : Api.Error -> String
errorMessage error =
    case error of
        Api.Network ->
            "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente."

        Api.Timeout ->
            "O servidor demorou para responder. Tente novamente."

        Api.InvalidResponse ->
            "O servidor retornou uma resposta inesperada. Tente novamente."

        Api.Rejected status code reasons _ ->
            case code of
                "invalid_credentials" ->
                    "E-mail ou senha incorretos. Confira seus dados e tente novamente."

                "email_taken" ->
                    "Este e-mail já está cadastrado. Use a opção Entrar para acessar sua conta."

                "invalid_email" ->
                    "O e-mail informado não é válido."

                "weak_password" ->
                    "A senha foi recusada. " ++ String.join " " (List.map passwordReason reasons)

                "invalid_request" ->
                    "Confira os dados informados e tente novamente."

                _ ->
                    if status == 429 then
                        "Muitas tentativas. Aguarde um momento e tente novamente."

                    else if status >= 500 then
                        "O serviço está temporariamente indisponível. Tente novamente em instantes."

                    else
                        "Não foi possível concluir a operação. Confira os dados e tente novamente."


passwordReason : String -> String
passwordReason reason =
    case reason of
        "too_short" ->
            "Use pelo menos 12 caracteres."

        "no_upper" ->
            "Inclua uma letra maiúscula."

        "no_lower" ->
            "Inclua uma letra minúscula."

        "no_digit" ->
            "Inclua um número."

        "no_symbol" ->
            "Inclua um símbolo."

        _ ->
            "Confira os requisitos da senha."


view : Model -> Html Msg
view model =
    div [ class "app-shell" ]
        [ aside [ class "story-panel" ]
            [ a [ href "/", class "brand", attribute "aria-label" "Saldo, início" ] [ span [ class "brand-mark", attribute "aria-hidden" "true" ] [ text "s" ], text "saldo" ]
            , div [ class "story-content" ]
                [ p [ class "eyebrow" ] [ text "SEU DINHEIRO, COM MAIS CLAREZA" ]
                , h1 [] [ text "Organize o presente.", br [] [], span [] [ text "Planeje o que vem." ] ]
                , p [ class "story-description" ] [ text "Um lugar para acompanhar suas finanças e dar mais espaço ao que importa para você." ]
                , div [ class "illustration", attribute "aria-hidden" "true" ]
                    [ div [ class "orbit orbit-one" ] []
                    , div [ class "orbit orbit-two" ] []
                    , div [ class "finance-card" ]
                        [ div [ class "card-top" ] [ span [] [ text "Uma visão mais clara" ], span [] [ text "↗" ] ]
                        , div [ class "decor-line" ] []
                        , div [ class "chart" ] (List.map (\n -> div [ class ("bar bar-" ++ String.fromInt n) ] []) (List.range 1 7))
                        , div [ class "card-bottom" ] [ span [] [ text "Cada passo conta." ], span [] [ text "+" ] ]
                        ]
                    , div [ class "floating-tag" ] [ span [ class "check-icon" ] [ text "✓" ], text "Tudo começa com organização" ]
                    ]
                ]
            , p [ class "story-footer" ] [ span [ class "tiny-dot" ] [], text "Mais organização. Mais possibilidades." ]
            ]
        , main_ [ class "main-panel" ]
            [ div [ class "mobile-brand" ] [ span [ class "brand-mark" ] [ text "s" ], text "saldo" ]
            , div [ class "form-container" ]
                [ case model.auth of
                    SignedOut ->
                        authView model

                    Checking _ ->
                        section [ class "session-card", attribute "aria-live" "polite", attribute "aria-busy" "true" ]
                            [ span [ class "spinner large" ] [], h2 [] [ text "Preparando seu acesso" ], p [ class "subtitle" ] [ text "Estamos verificando sua sessão." ] ]

                    SessionProblem _ message ->
                        section [ class "session-card" ]
                            [ h2 [] [ text "Não foi possível verificar sua sessão" ]
                            , div [ class "alert error", attribute "role" "alert" ] [ text message ]
                            , button [ class "primary", onClick RetryProfile ] [ text "Tentar novamente" ]
                            , button [ class "text-button", onClick Logout ] [ text "Voltar para o login" ]
                            ]

                    SignedIn _ profile ->
                        section [ class "session-card" ]
                            [ span [ class "success-seal", attribute "aria-hidden" "true" ] [ text "✓" ]
                            , p [ class "eyebrow dark" ] [ text "ACESSO CONFIRMADO" ]
                            , h2 [] [ text "Bem-vindo ao Saldo" ]
                            , p [ class "subtitle" ] [ text "Sua sessão está ativa." ]
                            , div [ class "profile-details" ] [ span [] [ text "E-mail da conta" ], strong [] [ text profile.email ] ]
                            , p [ class "next-step" ] [ text "Este é o início da sua área pessoal. As funcionalidades financeiras serão disponibilizadas nas próximas etapas do projeto." ]
                            , button [ class "primary", onClick Logout ] [ text "Sair da conta" ]
                            ]
                ]
            , footer [ class "main-footer" ] [ text "Seu próximo passo começa com clareza." ]
            ]
        ]


authView : Model -> Html Msg
authView model =
    let
        registering =
            isRegister model
    in
    section []
        [ div [ class "form-heading" ]
            [ p [ class "eyebrow dark" ] [ text "FINANÇAS PESSOAIS" ]
            , h2 []
                [ text
                    (if registering then
                        "Comece sua organização"

                     else
                        "Que bom ter você aqui"
                    )
                ]
            , p [ class "subtitle" ]
                [ text
                    (if registering then
                        "Crie sua conta e dê o primeiro passo."

                     else
                        "Entre para continuar cuidando das suas finanças."
                    )
                ]
            ]
        , div [ class "tabs", attribute "aria-label" "Opções de acesso" ]
            [ button
                [ type_ "button"
                , classList [ ( "tab", True ), ( "active", not registering ) ]
                , attribute "aria-pressed"
                    (if registering then
                        "false"

                     else
                        "true"
                    )
                , onClick (ChangePage Login)
                ]
                [ text "Entrar" ]
            , button
                [ type_ "button"
                , classList [ ( "tab", True ), ( "active", registering ) ]
                , attribute "aria-pressed"
                    (if registering then
                        "true"

                     else
                        "false"
                    )
                , onClick (ChangePage Register)
                ]
                [ text "Criar conta" ]
            ]
        , if String.isEmpty model.notice then
            text ""

          else
            div [ class "alert success", attribute "role" "status" ] [ text model.notice ]
        , if String.isEmpty model.error then
            text ""

          else
            div [ id "form-error", class "alert error", attribute "role" "alert" ] [ text model.error ]
        , Html.form
            [ onSubmit Submit
            , attribute "novalidate" ""
            , attribute "aria-busy"
                (if model.busy then
                    "true"

                 else
                    "false"
                )
            ]
            [ field model "email" "E-mail" "email" "voce@exemplo.com" model.email EmailChanged "email"
            , div [ class "password-field" ]
                [ field model
                    "password"
                    "Senha"
                    (if model.showPassword then
                        "text"

                     else
                        "password"
                    )
                    (if registering then
                        "Crie uma senha forte"

                     else
                        "Digite sua senha"
                    )
                    model.password
                    PasswordChanged
                    (if registering then
                        "new-password"

                     else
                        "current-password"
                    )
                , button
                    [ type_ "button"
                    , class "visibility-button"
                    , onClick TogglePassword
                    , attribute "aria-label"
                        (if model.showPassword then
                            "Ocultar senha"

                         else
                            "Mostrar senha"
                        )
                    , attribute "aria-pressed"
                        (if model.showPassword then
                            "true"

                         else
                            "false"
                        )
                    ]
                    [ text
                        (if model.showPassword then
                            "Ocultar"

                         else
                            "Mostrar"
                        )
                    ]
                ]
            , if registering then
                div [ class "registration-fields" ]
                    [ ul [ class "password-rules", id "password-requirements", attribute "aria-label" "Requisitos da senha" ]
                        (List.map
                            (\( labelText, met ) ->
                                li [ classList [ ( "met", met ) ] ]
                                    [ span [ attribute "aria-hidden" "true" ]
                                        [ text
                                            (if met then
                                                "✓"

                                             else
                                                "○"
                                            )
                                        ]
                                    , text labelText
                                    ]
                            )
                            (Validation.passwordRules model.password)
                        )
                    , field model
                        "confirmation"
                        "Confirme sua senha"
                        (if model.showPassword then
                            "text"

                         else
                            "password"
                        )
                        "Digite a senha novamente"
                        model.confirmation
                        ConfirmationChanged
                        "new-password"
                    ]

              else
                text ""
            , button [ type_ "submit", class "primary", disabled model.busy ]
                [ if model.busy then
                    span [ class "spinner", attribute "aria-hidden" "true" ] []

                  else
                    text ""
                , text
                    (if model.busy then
                        if registering then
                            "Criando sua conta…"

                        else
                            "Entrando…"

                     else if registering then
                        "Criar minha conta"

                     else
                        "Entrar na minha conta"
                    )
                , if model.busy then
                    text ""

                  else
                    span [ attribute "aria-hidden" "true" ] [ text " →" ]
                ]
            ]
        , p [ class "switch-prompt" ]
            [ text
                (if registering then
                    "Já tem uma conta? "

                 else
                    "Ainda não tem uma conta? "
                )
            , button
                [ class "text-button"
                , type_ "button"
                , onClick
                    (ChangePage
                        (if registering then
                            Login

                         else
                            Register
                        )
                    )
                ]
                [ text
                    (if registering then
                        "Entre aqui"

                     else
                        "Crie sua conta"
                    )
                ]
            ]
        , div [ class "privacy-note" ] [ span [ attribute "aria-hidden" "true" ] [ text "◈" ], p [] [ text "Acesso individual às suas finanças.", br [] [], text "Sua senha não é salva pela aplicação." ] ]
        ]


field : Model -> String -> String -> String -> String -> String -> (String -> Msg) -> String -> Html Msg
field model fieldId labelText inputType hint current toMsg autocompleteValue =
    let
        problem =
            if model.submitted then
                validationErrors model |> List.filter (\( name, _ ) -> name == fieldId) |> List.head |> Maybe.map Tuple.second

            else
                Nothing

        invalid =
            problem /= Nothing || List.member fieldId model.serverFields

        describedBy =
            String.join " "
                ((if problem /= Nothing then
                    [ fieldId ++ "-error" ]

                  else
                    []
                 )
                    ++ (if fieldId == "password" && isRegister model then
                            [ "password-requirements" ]

                        else
                            []
                       )
                    ++ (if List.member fieldId model.serverFields then
                            [ "form-error" ]

                        else
                            []
                       )
                )
    in
    div [ class "field" ]
        [ label [ for fieldId ] [ text labelText ]
        , input
            [ id fieldId
            , name fieldId
            , type_ inputType
            , placeholder hint
            , value current
            , onInput toMsg
            , attribute "autocomplete" autocompleteValue
            , required True
            , readonly model.busy
            , attribute "aria-invalid"
                (if invalid then
                    "true"

                 else
                    "false"
                )
            , attribute "aria-describedby" describedBy
            , attribute "autocapitalize" "none"
            , spellcheck False
            ]
            []
        , case problem of
            Just message ->
                p [ class "field-error", id (fieldId ++ "-error") ] [ text message ]

            Nothing ->
                text ""
        ]
