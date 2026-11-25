module Money exposing (amountInput, format, parseAmount)


format : Int -> String
format cents =
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


amountInput : Int -> String
amountInput cents =
    let
        digits =
            String.fromInt cents |> String.padLeft 3 '0'
    in
    String.dropRight 2 digits ++ "," ++ String.right 2 digits


parseAmount : String -> Maybe Int
parseAmount input =
    let
        isDigits part =
            not (String.isEmpty part) && String.all Char.isDigit part

        toCents whole fraction =
            if isDigits whole && isDigits fraction && String.length fraction <= 2 then
                String.toInt (whole ++ String.padRight 2 '0' fraction)
                    |> Maybe.andThen
                        (\cents ->
                            if cents > 0 && cents <= 9007199254740991 then
                                Just cents

                            else
                                Nothing
                        )

            else
                Nothing
    in
    case String.trim input |> String.replace "," "." |> String.split "." of
        [ whole ] ->
            toCents whole "00"

        [ whole, fraction ] ->
            toCents whole fraction

        _ ->
            Nothing
