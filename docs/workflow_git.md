# Organisation Git

| Élément | Règle |
|---|---|
| Branche `main` | Toujours verte (tests passent). On n'y pousse pas directement. |
| Branches de travail | `feature/<sujet>`, `refactor/<sujet>`, `test/<sujet>`, `docs/<sujet>` |
| Intégration | Pull request relue par l'autre membre avant fusion |
| Messages de commit | `type: résumé à l'impératif` avec `feat`, `refactor`, `test`, `docs`, `fix`, `chore` |
| Règle d'or | Jamais de refactoring et d'ajout de fonctionnalité dans le même commit |

Exemples : `refactor: extraire FormateurRapportTexte de GestionnaireBudget`,
`test: caractériser le calcul des alertes de la V1`.

Chaque refactoring « avant / après » de la soutenance = un commit identifiable, tag `avant-srp`,
`apres-srp`, etc.
