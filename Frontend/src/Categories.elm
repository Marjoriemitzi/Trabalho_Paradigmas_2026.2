module Categories exposing (Category, Kind(..), kindCode, kindDecoder, kindLabel, listDecoder, listRequest)

import Api
import Json.Decode as Decode
import Json.Encode as Encode


type Kind
    = Income
    | Expense


type alias Category =
    { kind : Kind
    , name : String
    , label : String
    }


kindCode : Kind -> String
kindCode kind =
    case kind of
        Income ->
            "income"

        Expense ->
            "expense"


kindLabel : Kind -> String
kindLabel kind =
    case kind of
        Income ->
            "Receita"

        Expense ->
            "Despesa"


kindDecoder : Decode.Decoder Kind
kindDecoder =
    Decode.string
        |> Decode.andThen
            (\code ->
                case code of
                    "income" ->
                        Decode.succeed Income

                    "expense" ->
                        Decode.succeed Expense

                    _ ->
                        Decode.fail "Tipo de lançamento desconhecido"
            )


listRequest : String -> Api.Request
listRequest requestId =
    { id = requestId, method = "GET", path = "/categories", body = Encode.null }


listDecoder : Decode.Decoder (List Category)
listDecoder =
    Decode.field "categories" <|
        Decode.list <|
            Decode.map3 Category
                (Decode.field "kind" kindDecoder)
                (Decode.field "name" Decode.string)
                (Decode.field "label" Decode.string)
