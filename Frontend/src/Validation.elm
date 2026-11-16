module Validation exposing (emailValid, passwordRules, problems)

import Char


emailValid : String -> Bool
emailValid email =
    let
        cleaned =
            String.trim email
    in
    String.length cleaned
        <= 254
        && not (List.any (\c -> List.member c [ ' ', '\t', '\n', '\u{000D}' ]) (String.toList cleaned))
        && (case String.split "@" cleaned of
                [ local, domain ] ->
                    not (String.isEmpty local)
                        && (case String.split "." domain of
                                first :: rest ->
                                    not (String.isEmpty first) && not (List.isEmpty rest) && List.all (not << String.isEmpty) rest

                                _ ->
                                    False
                           )

                _ ->
                    False
           )


passwordRules : String -> List ( String, Bool )
passwordRules password =
    let
        chars =
            String.toList password
    in
    [ ( "Pelo menos 12 caracteres", List.length chars >= 12 )
    , ( "Uma letra maiúscula", List.any Char.isUpper chars )
    , ( "Uma letra minúscula", List.any Char.isLower chars )
    , ( "Um número", List.any Char.isDigit chars )
    , ( "Um símbolo", List.any (not << Char.isAlphaNum) chars )
    ]


problems : Bool -> String -> String -> String -> List ( String, String )
problems registering email password confirmation =
    (if emailValid email then
        []

     else
        [ ( "email", "Informe um e-mail válido." ) ]
    )
        ++ (if String.isEmpty password then
                [ ( "password", "Informe sua senha." ) ]

            else if registering && not (List.all Tuple.second (passwordRules password)) then
                [ ( "password", "A senha precisa atender a todos os requisitos abaixo." ) ]

            else
                []
           )
        ++ (if registering && password /= confirmation then
                [ ( "confirmation", "As senhas não coincidem." ) ]

            else
                []
           )
