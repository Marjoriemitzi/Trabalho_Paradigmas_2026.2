:- module(categorization, [transaction_category/3, category_choice/2]).
:- encoding(utf8).

category_keyword(expense, mercado,    ["supermercado", "mercado", "hortifruti", "padaria", "acougue"]).
category_keyword(expense, transporte, ["uber", "taxi", "onibus", "metro", "combustivel", "posto"]).
category_keyword(expense, moradia,    ["aluguel", "condominio", "energia", "agua", "internet"]).
category_keyword(expense, lazer,      ["cinema", "netflix", "spotify", "show", "restaurante"]).
category_keyword(expense, saude,      ["farmacia", "consulta", "exame"]).
category_keyword(income,  salario,    ["salario", "folha de pagamento"]).
category_keyword(income,  freelance,  ["freela", "freelance"]).

transaction_category(Tipo, Descricao, Categoria) :-
    category_keyword(Tipo, Categoria, Palavras),
    member(Palavra, Palavras),
    sub_string(Descricao, _, _, _, Palavra),
    !.
transaction_category(_, _, outros).

category_choice(Tipo, Categoria) :- category_keyword(Tipo, Categoria, _).
category_choice(_, outros).
