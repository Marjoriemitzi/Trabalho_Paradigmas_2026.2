module Accounts exposing (Account, Kind(..), Model, Msg, init, kindLabel, listDecoder, listRequest, receive, update, view)

import Api
import Html exposing (Html, article, button, div, form, h2, h3, input, label, li, option, p, section, select, span, text, ul)
import Html.Attributes exposing (attribute, class, disabled, for, id, required, selected, type_, value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Json.Decode as Decode
import Json.Encode as Encode


type Kind
    = Wallet
    | Checking
    | CreditCard


type alias Account =
    { id : String
    , name : String
    , kind : Kind
    , balanceCents : Int
    }


type Listing
    = Loading
    | LoadFailed String
    | Loaded (List Account)


type Editor
    = Browsing
    | Creating String Kind
    | Renaming Account String
    | ConfirmingDelete Account


type alias Model =
    { listing : Listing
    , editor : Editor
    , saving : Bool
    , error : String
    , notice : String
    }


type Msg
    = Reload
    | StartCreate
    | StartRename Account
    | StartDelete Account
    | ChangeName String
    | ChangeKind String
    | Cancel
    | Save


init : ( Model, Cmd Msg )
init =
    load
        { listing = Loading
        , editor = Browsing
        , saving = False
        , error = ""
        , notice = ""
        }


listRequest : String -> Api.Request
listRequest requestId =
    { id = requestId, method = "GET", path = "/accounts", body = Encode.null }


listDecoder : Decode.Decoder (List Account)
listDecoder =
    Decode.field "accounts" <|
        Decode.list <|
            Decode.map4 Account
                (Decode.field "id" Decode.string)
                (Decode.field "name" Decode.string)
                (Decode.field "kind" kindDecoder)
                (Decode.field "balance_cents" Decode.int)


kindDecoder : Decode.Decoder Kind
kindDecoder =
    Decode.string
        |> Decode.andThen
            (\code ->
                case kindFromCode code of
                    Just kind ->
                        Decode.succeed kind

                    Nothing ->
                        Decode.fail "Tipo de conta desconhecido"
            )


kindFromCode : String -> Maybe Kind
kindFromCode code =
    case code of
        "wallet" ->
            Just Wallet

        "checking" ->
            Just Checking

        "credit_card" ->
            Just CreditCard

        _ ->
            Nothing


kindCode : Kind -> String
kindCode kind =
    case kind of
        Wallet ->
            "wallet"

        Checking ->
            "checking"

        CreditCard ->
            "credit_card"


kindLabel : Kind -> String
kindLabel kind =
    case kind of
        Wallet ->
            "Carteira"

        Checking ->
            "Conta corrente"

        CreditCard ->
            "Cartão de crédito"


load : Model -> ( Model, Cmd Msg )
load model =
    ( { model | listing = Loading, error = "" }
    , Api.request (listRequest "accounts.list")
    )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    if model.saving then
        ( model, Cmd.none )

    else
        edit msg model


edit : Msg -> Model -> ( Model, Cmd Msg )
edit msg model =
    case msg of
        Reload ->
            load (withEditor Browsing model)

        StartCreate ->
            ( withEditor (Creating "" Wallet) model, Cmd.none )

        StartRename account ->
            ( withEditor (Renaming account account.name) model, Cmd.none )

        StartDelete account ->
            ( withEditor (ConfirmingDelete account) model, Cmd.none )

        ChangeName name ->
            case model.editor of
                Creating _ kind ->
                    ( { model | editor = Creating name kind, error = "" }, Cmd.none )

                Renaming account _ ->
                    ( { model | editor = Renaming account name, error = "" }, Cmd.none )

                _ ->
                    ( model, Cmd.none )

        ChangeKind code ->
            case ( model.editor, kindFromCode code ) of
                ( Creating name _, Just kind ) ->
                    ( { model | editor = Creating name kind, error = "" }, Cmd.none )

                _ ->
                    ( model, Cmd.none )

        Cancel ->
            ( withEditor Browsing model, Cmd.none )

        Save ->
            save model


withEditor : Editor -> Model -> Model
withEditor editor model =
    { model | editor = editor, error = "", notice = "" }


save : Model -> ( Model, Cmd Msg )
save model =
    let
        submit method path body =
            ( { model | saving = True, error = "", notice = "" }
            , Api.request { id = "accounts.save", method = method, path = path, body = body }
            )

        saveName name method path extra =
            let
                trimmedName =
                    String.trim name
            in
            if String.isEmpty trimmedName then
                ( { model | error = "Informe o nome da conta." }, Cmd.none )

            else
                submit method path (Encode.object (( "name", Encode.string trimmedName ) :: extra))
    in
    case model.editor of
        Creating name kind ->
            saveName name "POST" "/accounts" [ ( "kind", Encode.string (kindCode kind) ) ]

        Renaming account name ->
            saveName name "PATCH" ("/accounts/" ++ account.id) []

        ConfirmingDelete account ->
            submit "DELETE" ("/accounts/" ++ account.id) Encode.null

        Browsing ->
            ( model, Cmd.none )


receive : Api.Response -> Model -> ( Model, Cmd Msg )
receive response model =
    case ( response.id, model.listing ) of
        ( "accounts.list", Loading ) ->
            let
                listing =
                    if response.status == 200 then
                        case Decode.decodeValue listDecoder response.body of
                            Ok accounts ->
                                Loaded accounts

                            Err _ ->
                                LoadFailed "O servidor retornou uma lista de contas inválida."

                    else
                        LoadFailed (errorMessage "Não foi possível carregar as contas." response)
            in
            ( { model | listing = listing }, Cmd.none )

        ( "accounts.save", _ ) ->
            if model.saving then
                receiveSave response model

            else
                ( model, Cmd.none )

        _ ->
            ( model, Cmd.none )


receiveSave : Api.Response -> Model -> ( Model, Cmd Msg )
receiveSave response model =
    let
        succeeded notice =
            load { model | editor = Browsing, saving = False, notice = notice }

        failed =
            ( { model | saving = False, error = errorMessage "Não foi possível concluir a operação." response }
            , Cmd.none
            )
    in
    case ( model.editor, response.status ) of
        ( Creating _ _, 201 ) ->
            succeeded "Conta criada."

        ( Renaming _ _, 200 ) ->
            succeeded "Conta renomeada."

        ( ConfirmingDelete _, 204 ) ->
            succeeded "Conta excluída."

        _ ->
            failed


errorMessage : String -> Api.Response -> String
errorMessage fallback response =
    case response.error of
        Just "account_name_taken" ->
            "Já existe uma conta com esse nome."

        Just "account_in_use" ->
            "Esta conta tem transações ou transferências e não pode ser excluída."

        Just "account_not_found" ->
            "A conta não está mais disponível. Atualize a lista."

        Just "invalid_account" ->
            "Confira o nome da conta (até 60 caracteres) e o tipo selecionado."

        Just "network_error" ->
            "Não foi possível conectar ao servidor. Tente novamente."

        Just "timeout" ->
            "O servidor demorou para responder. Atualize a lista antes de tentar novamente."

        _ ->
            fallback


view : Model -> Html Msg
view model =
    section [ class "accounts", attribute "aria-labelledby" "accounts-title" ]
        [ h2 [ id "accounts-title" ] [ text "Contas financeiras" ]
        , if String.isEmpty model.notice then
            text ""

          else
            p [ attribute "role" "status" ] [ text model.notice ]
        , case model.listing of
            Loading ->
                p [ attribute "role" "status" ] [ text "Carregando contas…" ]

            LoadFailed message ->
                div []
                    [ p [ attribute "role" "alert" ] [ text message ]
                    , action "Tentar novamente" Reload False
                    ]

            Loaded accounts ->
                case model.editor of
                    Browsing ->
                        div []
                            [ div [ class "account-actions" ]
                                [ action "Nova conta" StartCreate False
                                , action "Atualizar lista" Reload False
                                ]
                            , if List.isEmpty accounts then
                                p [] [ text "Você ainda não tem contas cadastradas." ]

                              else
                                ul [ class "account-list" ] (List.map accountRow accounts)
                            ]

                    Creating name kind ->
                        editorForm "Nova conta" name (Just kind) model

                    Renaming account name ->
                        editorForm ("Renomear " ++ account.name) name Nothing model

                    ConfirmingDelete account ->
                        div []
                            [ h3 [] [ text "Excluir conta" ]
                            , p [] [ text ("Deseja excluir a conta “" ++ account.name ++ "”?") ]
                            , errorView model.error
                            , div [ class "account-actions" ]
                                [ action "Confirmar exclusão" Save model.saving
                                , action "Cancelar" Cancel model.saving
                                ]
                            ]
        ]


accountRow : Account -> Html Msg
accountRow account =
    li []
        [ article [ class "account-row" ]
            [ div []
                [ h3 [] [ text account.name ]
                , p [] [ span [] [ text (kindLabel account.kind) ], text (" · " ++ formatBalance account.balanceCents) ]
                ]
            , div [ class "account-actions" ]
                [ action "Renomear" (StartRename account) False
                , action "Excluir" (StartDelete account) False
                ]
            ]
        ]


formatBalance : Int -> String
formatBalance cents =
    let
        digits =
            String.fromInt (abs cents) |> String.padLeft 3 '0'

        sign =
            if cents < 0 then
                "-"

            else
                ""
    in
    sign
        ++ "R$ "
        ++ groupThousands (String.dropRight 2 digits)
        ++ ","
        ++ String.right 2 digits


groupThousands : String -> String
groupThousands digits =
    if String.length digits <= 3 then
        digits

    else
        groupThousands (String.dropRight 3 digits) ++ "." ++ String.right 3 digits


editorForm : String -> String -> Maybe Kind -> Model -> Html Msg
editorForm heading name kind model =
    form [ onSubmit Save ]
        [ h3 [] [ text heading ]
        , label [ for "account-name" ] [ text "Nome da conta" ]
        , input
            [ id "account-name", value name, onInput ChangeName, required True, disabled model.saving ]
            []
        , case kind of
            Just chosen ->
                div []
                    [ label [ for "account-kind" ] [ text "Tipo de conta" ]
                    , select [ id "account-kind", onInput ChangeKind, disabled model.saving ]
                        (List.map
                            (\item -> option [ value (kindCode item), selected (item == chosen) ] [ text (kindLabel item) ])
                            [ Wallet, Checking, CreditCard ]
                        )
                    ]

            Nothing ->
                text ""
        , errorView model.error
        , div [ class "account-actions" ]
            [ button [ type_ "submit", disabled model.saving ] [ text "Salvar" ]
            , action "Cancelar" Cancel model.saving
            ]
        ]


errorView : String -> Html Msg
errorView message =
    if String.isEmpty message then
        text ""

    else
        p [ attribute "role" "alert" ] [ text message ]


action : String -> Msg -> Bool -> Html Msg
action caption msg unavailable =
    button [ type_ "button", onClick msg, disabled unavailable ] [ text caption ]
