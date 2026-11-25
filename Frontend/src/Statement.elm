module Statement exposing (Model, Msg, init, receive, update, view)

import Accounts
import Api
import Categories exposing (Category, Kind(..))
import Html exposing (Html, article, button, dd, div, dl, dt, form, h2, h3, h4, input, label, li, option, p, section, select, text, ul)
import Html.Attributes exposing (attribute, class, disabled, for, id, required, selected, type_, value)
import Html.Events exposing (onClick, onInput, onSubmit)
import Json.Decode as Decode
import Json.Encode as Encode
import Money
import StatementData exposing (Entry, Statement, Transfer)


type alias Filters =
    { from : String, to : String, accountId : String }


type alias Draft =
    { accountId : String
    , kind : Kind
    , amount : String
    , description : String
    , occurredOn : String
    , category : String
    }


type Listing
    = AwaitingFilters
    | Loading Filters
    | Loaded Filters Statement
    | Failed Filters String


type Catalog
    = Unrequested
    | CatalogLoading
    | CatalogReady (List Category)
    | CatalogFailed


type Editor
    = Editing (Maybe String) Draft
    | ConfirmDelete Entry


type alias Model =
    { filters : Filters
    , listing : Listing
    , catalog : Catalog
    , editor : Maybe Editor
    , saving : Bool
    , filterError : String
    , saveError : String
    , notice : String
    }


type Msg
    = ChangeFilters (Filters -> Filters)
    | ApplyFilters
    | NewEntry String
    | EditEntry Entry
    | DeleteEntry Entry
    | EditDraft (Draft -> Draft)
    | LoadCatalog
    | Cancel
    | Save


init : Model
init =
    { filters = { from = "", to = "", accountId = "" }
    , listing = AwaitingFilters
    , catalog = Unrequested
    , editor = Nothing
    , saving = False
    , filterError = ""
    , saveError = ""
    , notice = ""
    }


isLoading : Listing -> Bool
isLoading listing =
    case listing of
        Loading _ ->
            True

        _ ->
            False


load : Filters -> Model -> ( Model, Cmd Msg )
load filters model =
    let
        accountQuery =
            if String.isEmpty filters.accountId then
                ""

            else
                "&account_id=" ++ filters.accountId

        ( withCatalog, catalogRequest ) =
            ensureCatalog model
    in
    ( { withCatalog | listing = Loading filters, filterError = "" }
    , Cmd.batch
        [ Api.request
            { id = "statement.list"
            , method = "GET"
            , path = "/transactions?from=" ++ filters.from ++ "&to=" ++ filters.to ++ accountQuery
            , body = Encode.null
            }
        , catalogRequest
        ]
    )


ensureCatalog : Model -> ( Model, Cmd Msg )
ensureCatalog model =
    case model.catalog of
        Unrequested ->
            loadCatalog model

        _ ->
            ( model, Cmd.none )


loadCatalog : Model -> ( Model, Cmd Msg )
loadCatalog model =
    ( { model | catalog = CatalogLoading }, Api.request (Categories.listRequest "statement.categories") )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    if model.saving || isLoading model.listing then
        ( model, Cmd.none )

    else
        case msg of
            ChangeFilters change ->
                ( { model | filters = change model.filters, filterError = "" }, Cmd.none )

            ApplyFilters ->
                if String.isEmpty model.filters.from || String.isEmpty model.filters.to then
                    ( { model | filterError = "Informe as duas datas do período." }, Cmd.none )

                else if model.filters.from > model.filters.to then
                    ( { model | filterError = "A data inicial deve ser anterior ou igual à final." }, Cmd.none )

                else
                    load model.filters { model | notice = "" }

            NewEntry accountId ->
                openEditor
                    (Editing Nothing
                        { accountId = accountId
                        , kind = Expense
                        , amount = ""
                        , description = ""
                        , occurredOn = model.filters.to
                        , category = ""
                        }
                    )
                    model

            EditEntry entry ->
                openEditor
                    (Editing (Just entry.id)
                        { accountId = entry.accountId
                        , kind = entry.kind
                        , amount = Money.amountInput entry.amountCents
                        , description = entry.description
                        , occurredOn = entry.occurredOn
                        , category = entry.category
                        }
                    )
                    model

            DeleteEntry entry ->
                ( { model | editor = Just (ConfirmDelete entry), saveError = "", notice = "" }, Cmd.none )

            EditDraft change ->
                case model.editor of
                    Just (Editing entryId draft) ->
                        ( { model | editor = Just (Editing entryId (change draft)), saveError = "" }, Cmd.none )

                    _ ->
                        ( model, Cmd.none )

            LoadCatalog ->
                loadCatalog model

            Cancel ->
                ( { model | editor = Nothing, saveError = "" }, Cmd.none )

            Save ->
                save model


openEditor : Editor -> Model -> ( Model, Cmd Msg )
openEditor editor model =
    ensureCatalog { model | editor = Just editor, saveError = "", notice = "" }


save : Model -> ( Model, Cmd Msg )
save model =
    let
        submit method path body =
            ( { model | saving = True, saveError = "" }
            , Api.request { id = "statement.save", method = method, path = path, body = body }
            )

        invalid explanation =
            ( { model | saveError = explanation }, Cmd.none )
    in
    case model.editor of
        Just (ConfirmDelete entry) ->
            submit "DELETE" ("/transactions/" ++ entry.id) Encode.null

        Just (Editing entryId draft) ->
            case Money.parseAmount draft.amount of
                Nothing ->
                    invalid "Informe um valor positivo, com até duas casas decimais."

                Just amount ->
                    if String.isEmpty draft.accountId || String.isEmpty draft.occurredOn || String.isEmpty (String.trim draft.description) then
                        invalid "Preencha a conta, a data e a descrição."

                    else
                        let
                            body =
                                Encode.object
                                    [ ( "account_id", Encode.string draft.accountId )
                                    , ( "kind", Encode.string (Categories.kindCode draft.kind) )
                                    , ( "amount_cents", Encode.int amount )
                                    , ( "description", Encode.string (String.trim draft.description) )
                                    , ( "occurred_on", Encode.string draft.occurredOn )
                                    , ( "category"
                                      , if String.isEmpty draft.category then
                                            Encode.null

                                        else
                                            Encode.string draft.category
                                      )
                                    ]
                        in
                        case entryId of
                            Just entry ->
                                submit "PUT" ("/transactions/" ++ entry) body

                            Nothing ->
                                submit "POST" "/transactions" body

        Nothing ->
            ( model, Cmd.none )


receive : Api.Response -> Model -> ( Model, Cmd Msg, Bool )
receive response model =
    case ( response.id, model.listing ) of
        ( "statement.list", Loading filters ) ->
            let
                listing =
                    if response.status == 200 then
                        case Decode.decodeValue StatementData.decoder response.body of
                            Ok statement ->
                                Loaded filters statement

                            Err _ ->
                                Failed filters "O servidor retornou um extrato inválido."

                    else
                        Failed filters (errorMessage "Não foi possível carregar o extrato." response)
            in
            ( { model | listing = listing }, Cmd.none, False )

        ( "statement.categories", _ ) ->
            let
                catalog =
                    if response.status == 200 then
                        Decode.decodeValue Categories.listDecoder response.body
                            |> Result.map CatalogReady
                            |> Result.withDefault CatalogFailed

                    else
                        CatalogFailed
            in
            ( { model | catalog = catalog }, Cmd.none, False )

        ( "statement.save", _ ) ->
            if model.saving then
                receiveSave response model

            else
                ( model, Cmd.none, False )

        _ ->
            ( model, Cmd.none, False )


receiveSave : Api.Response -> Model -> ( Model, Cmd Msg, Bool )
receiveSave response model =
    let
        succeeded notice day =
            let
                next =
                    { model | saving = False, editor = Nothing, notice = notice }

                ( loaded, command ) =
                    case model.listing of
                        Loaded filters _ ->
                            load filters next

                        Failed filters _ ->
                            load filters next

                        _ ->
                            let
                                filters =
                                    { from = day, to = day, accountId = "" }
                            in
                            load filters { next | filters = filters }
            in
            ( loaded, command, True )
    in
    case ( model.editor, response.status ) of
        ( Just (Editing Nothing draft), 201 ) ->
            succeeded "Lançamento criado." draft.occurredOn

        ( Just (Editing (Just _) draft), 200 ) ->
            succeeded "Lançamento atualizado." draft.occurredOn

        ( Just (ConfirmDelete entry), 204 ) ->
            succeeded "Lançamento excluído." entry.occurredOn

        _ ->
            ( { model | saving = False, saveError = errorMessage "Não foi possível salvar a alteração." response }
            , Cmd.none
            , False
            )


errorMessage : String -> Api.Response -> String
errorMessage fallback response =
    case response.error of
        Just "invalid_period" ->
            "Informe um período válido, com até 366 dias incluindo a data final."

        Just "account_not_found" ->
            "A conta não está disponível. Atualize as contas ou escolha outra."

        Just "transaction_not_found" ->
            "O lançamento não está mais disponível. Consulte o extrato novamente."

        Just "invalid_transaction" ->
            "Confira a conta, a categoria, o valor ou a descrição (até 200 caracteres)."

        Just "network_error" ->
            "Não foi possível conectar ao servidor."

        Just "timeout" ->
            "O servidor demorou para responder. Consulte o extrato antes de repetir a operação."

        _ ->
            fallback


view : List Accounts.Account -> Model -> Html Msg
view accounts model =
    let
        busy =
            isLoading model.listing || model.saving

        categories =
            case model.catalog of
                CatalogReady items ->
                    items

                _ ->
                    []
    in
    section [ class "statement", attribute "aria-labelledby" "statement-title" ]
        [ h2 [ id "statement-title" ] [ text "Extrato e lançamentos" ]
        , message "status" model.notice
        , case model.editor of
            Just (Editing _ draft) ->
                viewEditor accounts draft model

            Just (ConfirmDelete entry) ->
                div []
                    [ h3 [] [ text "Excluir lançamento" ]
                    , p [] [ text ("Deseja excluir “" ++ entry.description ++ "”?") ]
                    , message "alert" model.saveError
                    , div [ class "account-actions" ]
                        [ action "Confirmar exclusão" Save busy
                        , action "Cancelar" Cancel busy
                        ]
                    ]

            Nothing ->
                div []
                    [ viewFilters accounts model
                    , div [ class "account-actions" ]
                        [ action "Novo lançamento"
                            (NewEntry (defaultAccount model.filters.accountId accounts))
                            (busy || List.isEmpty accounts)
                        ]
                    , if List.isEmpty accounts then
                        p [] [ text "Para lançar receitas ou despesas, cadastre uma conta financeira." ]

                      else
                        text ""
                    , case model.listing of
                        AwaitingFilters ->
                            text ""

                        Loading _ ->
                            message "status" "Carregando extrato…"

                        Failed _ error ->
                            message "alert" error

                        Loaded filters statement ->
                            viewStatement accounts categories filters statement
                    ]
        ]


defaultAccount : String -> List Accounts.Account -> String
defaultAccount current accounts =
    if List.any (\account -> account.id == current) accounts then
        current

    else
        List.head accounts |> Maybe.map .id |> Maybe.withDefault ""


viewFilters : List Accounts.Account -> Model -> Html Msg
viewFilters accounts model =
    let
        busy =
            isLoading model.listing || model.saving
    in
    form [ onSubmit ApplyFilters ]
        [ div [ class "statement-filters" ]
            [ field "statement-from" "Data inicial" "date" model.filters.from (\v -> ChangeFilters (\f -> { f | from = v })) busy
            , field "statement-to" "Data final" "date" model.filters.to (\v -> ChangeFilters (\f -> { f | to = v })) busy
            , accountSelect "statement-account"
                "Filtrar por conta"
                "Todas as contas"
                accounts
                model.filters.accountId
                (\v -> ChangeFilters (\f -> { f | accountId = v }))
                busy
            ]
        , message "alert" model.filterError
        , div [ class "account-actions" ]
            [ button [ type_ "submit", disabled busy ] [ text "Consultar extrato" ] ]
        ]


viewEditor : List Accounts.Account -> Draft -> Model -> Html Msg
viewEditor accounts draft model =
    let
        categoryOptions =
            case model.catalog of
                CatalogReady categories ->
                    List.filter (\category -> category.kind == draft.kind) categories

                _ ->
                    []

        previousCategory =
            if String.isEmpty draft.category || List.any (\category -> category.name == draft.category) categoryOptions then
                []

            else
                [ choice draft.category draft.category draft.category ]
    in
    form [ onSubmit Save ]
        [ h3 [] [ text "Dados do lançamento" ]
        , accountSelect "entry-account"
            "Conta do lançamento"
            "Selecione"
            accounts
            draft.accountId
            (\v -> EditDraft (\d -> { d | accountId = v }))
            model.saving
        , div []
            [ label [ for "entry-kind" ] [ text "Tipo de lançamento" ]
            , select
                [ id "entry-kind"
                , disabled model.saving
                , onInput
                    (\code ->
                        let
                            kind =
                                if code == "income" then
                                    Income

                                else
                                    Expense
                        in
                        EditDraft (\d -> { d | kind = kind, category = "" })
                    )
                ]
                (List.map
                    (\kind -> choice (Categories.kindCode draft.kind) (Categories.kindCode kind) (Categories.kindLabel kind))
                    [ Expense, Income ]
                )
            ]
        , div []
            [ label [ for "entry-amount" ] [ text "Valor em reais" ]
            , input
                [ id "entry-amount"
                , type_ "text"
                , attribute "inputmode" "decimal"
                , Html.Attributes.placeholder "Ex. 15,90"
                , value draft.amount
                , required True
                , disabled model.saving
                , onInput (\v -> EditDraft (\d -> { d | amount = v }))
                ]
                []
            ]
        , field "entry-description" "Descrição" "text" draft.description (\v -> EditDraft (\d -> { d | description = v })) model.saving
        , field "entry-date" "Data do lançamento" "date" draft.occurredOn (\v -> EditDraft (\d -> { d | occurredOn = v })) model.saving
        , div []
            [ label [ for "entry-category" ] [ text "Categoria" ]
            , select
                [ id "entry-category"
                , disabled model.saving
                , onInput (\v -> EditDraft (\d -> { d | category = v }))
                ]
                (choice draft.category "" "Classificar automaticamente"
                    :: (previousCategory ++ List.map (\category -> choice draft.category category.name category.label) categoryOptions)
                )
            , case model.catalog of
                CatalogFailed ->
                    div [ class "account-actions" ] [ action "Recarregar categorias" LoadCatalog model.saving ]

                CatalogLoading ->
                    message "status" "Carregando categorias…"

                _ ->
                    text ""
            ]
        , message "alert" model.saveError
        , div [ class "account-actions" ]
            [ button [ type_ "submit", disabled model.saving ] [ text "Salvar lançamento" ]
            , action "Cancelar" Cancel model.saving
            ]
        ]


viewStatement : List Accounts.Account -> List Category -> Filters -> Statement -> Html Msg
viewStatement accounts categories filters statement =
    div []
        [ h3 [] [ text ("Extrato de " ++ displayDate filters.from ++ " a " ++ displayDate filters.to) ]
        , dl [ class "statement-totals" ]
            (List.map
                (\( name, amount ) -> div [] [ dt [] [ text name ], dd [] [ text (Money.format amount) ] ])
                ([ ( "Saldo inicial", statement.opening )
                 , ( "Receitas", statement.income )
                 , ( "Despesas", statement.expense )
                 ]
                    ++ (if String.isEmpty filters.accountId then
                            []

                        else
                            [ ( "Transferências recebidas", statement.transfersIn ), ( "Transferências enviadas", statement.transfersOut ) ]
                       )
                    ++ [ ( "Saldo final", statement.closing ) ]
                )
            )
        , h3 [] [ text "Lançamentos do período" ]
        , if List.isEmpty statement.entries then
            p [] [ text "Nenhum lançamento no período." ]

          else
            ul [ class "account-list" ] (List.map (viewEntry accounts categories) statement.entries)
        , if String.isEmpty filters.accountId || List.isEmpty statement.transfers then
            text ""

          else
            div []
                [ h3 [] [ text "Transferências do período" ]
                , ul [ class "account-list" ] (List.map (viewTransfer accounts) statement.transfers)
                ]
        ]


viewEntry : List Accounts.Account -> List Category -> Entry -> Html Msg
viewEntry accounts categories entry =
    let
        category =
            categories
                |> List.filter (\item -> item.kind == entry.kind && item.name == entry.category)
                |> List.head
                |> Maybe.map .label
                |> Maybe.withDefault entry.category
    in
    li []
        [ article [ class "account-row statement-row" ]
            [ div []
                [ h4 [] [ text entry.description ]
                , p [] [ text (displayDate entry.occurredOn ++ " · " ++ accountName accounts entry.accountId ++ " · " ++ category) ]
                , p [] [ text (Categories.kindLabel entry.kind ++ " · " ++ Money.format entry.amountCents) ]
                ]
            , div [ class "account-actions" ]
                [ action "Editar lançamento" (EditEntry entry) False
                , action "Excluir lançamento" (DeleteEntry entry) False
                ]
            ]
        ]


viewTransfer : List Accounts.Account -> Transfer -> Html Msg
viewTransfer accounts transfer =
    li []
        [ article [ class "account-row statement-row" ]
            [ div []
                [ h4 [] [ text transfer.description ]
                , p []
                    [ text (displayDate transfer.occurredOn ++ " · " ++ accountName accounts transfer.fromAccount ++ " → " ++ accountName accounts transfer.toAccount) ]
                ]
            , p [] [ text (Money.format transfer.amountCents) ]
            ]
        ]


accountName : List Accounts.Account -> String -> String
accountName accounts accountId =
    accounts
        |> List.filter (\account -> account.id == accountId)
        |> List.head
        |> Maybe.map .name
        |> Maybe.withDefault "Conta indisponível"


displayDate : String -> String
displayDate date =
    String.split "-" date |> List.reverse |> String.join "/"


accountSelect : String -> String -> String -> List Accounts.Account -> String -> (String -> Msg) -> Bool -> Html Msg
accountSelect fieldId caption empty accounts chosen change locked =
    let
        missing =
            if String.isEmpty chosen || List.any (\account -> account.id == chosen) accounts then
                []

            else
                [ choice chosen chosen "Conta indisponível" ]
    in
    div []
        [ label [ for fieldId ] [ text caption ]
        , select [ id fieldId, onInput change, disabled locked ]
            (choice chosen "" empty
                :: (missing ++ List.map (\account -> choice chosen account.id account.name) accounts)
            )
        ]


choice : String -> String -> String -> Html Msg
choice chosen code caption =
    option [ value code, selected (chosen == code) ] [ text caption ]


field : String -> String -> String -> String -> (String -> Msg) -> Bool -> Html Msg
field fieldId caption fieldType current change locked =
    div []
        [ label [ for fieldId ] [ text caption ]
        , input [ id fieldId, type_ fieldType, value current, onInput change, required True, disabled locked ] []
        ]


action : String -> Msg -> Bool -> Html Msg
action caption msg locked =
    button [ type_ "button", onClick msg, disabled locked ] [ text caption ]


message : String -> String -> Html Msg
message role content =
    if String.isEmpty content then
        text ""

    else
        p [ attribute "role" role ] [ text content ]
