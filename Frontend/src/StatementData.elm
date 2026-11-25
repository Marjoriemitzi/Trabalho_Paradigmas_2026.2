module StatementData exposing (Entry, Statement, Transfer, decoder)

import Categories exposing (Kind)
import Json.Decode as Decode


type alias Entry =
    { id : String
    , accountId : String
    , kind : Kind
    , amountCents : Int
    , description : String
    , category : String
    , occurredOn : String
    }


type alias Transfer =
    { fromAccount : String
    , toAccount : String
    , amountCents : Int
    , description : String
    , occurredOn : String
    }


type alias Statement =
    { opening : Int
    , income : Int
    , expense : Int
    , closing : Int
    , transfersIn : Int
    , transfersOut : Int
    , entries : List Entry
    , transfers : List Transfer
    }


decoder : Decode.Decoder Statement
decoder =
    Decode.map8 Statement
        (Decode.field "opening_balance_cents" Decode.int)
        (Decode.field "income_cents" Decode.int)
        (Decode.field "expense_cents" Decode.int)
        (Decode.field "closing_balance_cents" Decode.int)
        (Decode.field "transfers_in_cents" Decode.int)
        (Decode.field "transfers_out_cents" Decode.int)
        (Decode.field "transactions" (Decode.list entryDecoder))
        (Decode.field "transfers" (Decode.list transferDecoder))


entryDecoder : Decode.Decoder Entry
entryDecoder =
    Decode.map7 Entry
        (Decode.field "id" Decode.string)
        (Decode.field "account_id" Decode.string)
        (Decode.field "kind" Categories.kindDecoder)
        (Decode.field "amount_cents" Decode.int)
        (Decode.field "description" Decode.string)
        (Decode.field "category" Decode.string)
        (Decode.field "occurred_on" Decode.string)


transferDecoder : Decode.Decoder Transfer
transferDecoder =
    Decode.map5 Transfer
        (Decode.field "from_account_id" Decode.string)
        (Decode.field "to_account_id" Decode.string)
        (Decode.field "amount_cents" Decode.int)
        (Decode.field "description" Decode.string)
        (Decode.field "occurred_on" Decode.string)
