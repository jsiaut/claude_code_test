# Consignes pour Claude Code

Dépôt public. Ce fichier résume les invariants d'exploitation ; en cas d'écart, `SPEC.md`, `decisions.md` et
`config.yaml` l'emportent (D-0079). Le dépôt, ses décisions et les rapports à l'utilisateur sont en français.

## Avant de commencer

- Lire `delta.md` (ce qui a changé à la dernière exécution), puis `README.md` (prérequis, ordre d'une exécution).
- `decisions.md` est chronologique et long : y chercher une décision par son numéro (`grep -n "D-0078"`), sans le
  lire d'un bloc. La dernière dit où en est le travail.
- Avant un travail qui écrit, prendre le verrou de session, et le lever à la fin (§11.5, `pipeline/lock.py`) :
  `python3 -c "from pipeline import config, lock; lock.acquire(config.as_of(), label='<tâche>')"`, puis
  `python3 -c "from pipeline import lock; lock.release()"`.

## Invariants

- L'as_of n'a qu'une source, la clé `as_of` de `config.yaml`, jamais la date du jour (D-0073).
- Réseau SEC (§9.5) : une seule commande réseau à la fois, 5 requêtes par seconde au plus, une pause d'au moins
  10 minutes après un 403, aucun changement d'identité. Chaque requête va au journal (`journal.jsonl`).
- User-Agent : `secrets/user_agent.txt` (non versionné) ou `SEC_USER_AGENT`, envoyé aux seuls hôtes de la SEC. Ne
  jamais afficher ce fichier, ni écrire l'adresse de contact dans le dépôt (contrôle ci-dessous). L'adresse de
  courriel du compte de l'utilisateur ne va ni dans le dépôt ni dans une requête.
- Les critères des annexes E et F et les seuils sont commités avant toute requête ; tout changement ultérieur est
  signalé dans la note (§11.1, annexe B).
- Aucune ligne chargée ne nomme une personne physique (contrepartie, payeur, receveur, citation, note) : la fonction
  remplace le nom, une citation se réduit à un passage sans nom (D-0078 ; garde : `tests/test_d0078.py`).

## Méthode

- Chaque décision va dans `decisions.md` sous le numéro suivant (D-nnnn) : origine, constat, règles fixées avant
  tout tirage, toute lecture et tout changement de code, puis résultats. Un écart à une règle s'y consigne.
- Volume mesuré et consigné avant toute lecture. L'exécutant lit lui-même, un bloc à la fois
  (`python3 -m pipeline.reader status`, `show`, `submit` ; `lot` et `submit-lot` pour les petits blocs). Jamais de
  sous-agent : ils consomment les limites d'usage de l'utilisateur.
- Relecture : une liste `work/lists/<nom>.txt` et sa passe `work/tmp/run_<nom>.json`, avec `--list` ; la passe la
  plus récente remplace l'ancienne au chargement. Une passe sans lecture nouvelle (correction) s'inscrit dans
  `reading.correction_passes` de `config.yaml` (D-0078).
- `assemble` (10 à 15 minutes) puis `render`, en arrière-plan, jamais en même temps. Après un réassemblage,
  comparer les tables à celles du commit précédent et expliquer chaque écart dans la décision.

## Git

- `make check` (ruff, puis les tests) avant chaque commit ; le crochet le lance une fois activé dans le clone :
  `git config core.hooksPath .githooks`.
- Avant chaque commit, vérifier que l'adresse de contact n'est pas dans l'index (la commande doit afficher 0) :

  ```
  python3 -c "import os,re,subprocess as s; u=os.environ.get('SEC_USER_AGENT') or open('secrets/user_agent.txt').read(); print(sum(s.run(['git','diff','--cached'],capture_output=True,text=True).stdout.count(a) for a in set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+',u))))"
  ```
- Ni pull request, ni tâche planifiée de l'exécution périodique (§11.5), sans demande de l'utilisateur.
- Clone partiel (`git clone --filter=blob:none`) ou complet, jamais `--depth 1` (README, D-0079).
- Rapports à l'utilisateur : courts, en français.
