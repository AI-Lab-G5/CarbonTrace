# Executado dentro do grupo de concorrência de cada publicação de produção.
set -euo pipefail
head_sha=$(gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main" --jq '.object.sha')
if [[ "$head_sha" == "$GITHUB_SHA" ]]; then
  echo 'current=true' >> "$GITHUB_OUTPUT"
else
  echo "Publicação ignorada: main está em $head_sha e esta execução é de $GITHUB_SHA."
  echo 'current=false' >> "$GITHUB_OUTPUT"
fi
