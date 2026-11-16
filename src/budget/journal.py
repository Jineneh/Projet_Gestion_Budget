"""Journal : conservation et filtrage des transactions."""
from collections.abc import Iterable, Iterator

from budget.modeles import Transaction, TypeTransaction


class Journal:
    """Regroupe les transactions ; la liste interne n'est jamais exposée."""

    def __init__(self, transactions: Iterable[Transaction] = ()) -> None:
        self._transactions: list[Transaction] = []
        for transaction in transactions:
            self.ajouter(transaction)

    def ajouter(self, transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("Seules des Transaction peuvent être ajoutées au journal")
        self._transactions.append(transaction)

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        """Copie en lecture seule : modifier le résultat ne modifie pas le journal."""
        return tuple(self._transactions)

    def filtrer(
        self,
        mois: str | None = None,
        categorie: str | None = None,
        type_transaction: TypeTransaction | None = None,
    ) -> tuple[Transaction, ...]:
        """Renvoie les transactions qui respectent TOUS les critères fournis."""
        return tuple(
            transaction
            for transaction in self._transactions
            if (mois is None or transaction.mois == mois)
            and (categorie is None or transaction.categorie == categorie)
            and (type_transaction is None or transaction.type is type_transaction)
        )

    def depenses_du_mois(self, mois: str) -> tuple[Transaction, ...]:
        return self.filtrer(mois=mois, type_transaction=TypeTransaction.DEPENSE)

    def revenus_du_mois(self, mois: str) -> tuple[Transaction, ...]:
        return self.filtrer(mois=mois, type_transaction=TypeTransaction.REVENU)

    def __len__(self) -> int:
        return len(self._transactions)

    def __iter__(self) -> Iterator[Transaction]:
        return iter(self.transactions)
