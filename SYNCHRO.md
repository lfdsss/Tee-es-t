# SYNCHRO — Source de vérité /togo

> Lu au démarrage de /togo. Mis à jour après chaque décision.
> > Posture : pragmatique, ambitieuse, décisive. Pas de chantier annexe inventé.
> >
> > ## Repos suivis
> >
> > | Repo | Branche | Dernier commit poussé | CI | PR ouverte |
> > |---|---|---|---|---|
> > | nextjs | main | d1da335 | vert | — |
> > | prisme | main | 1cb763c | vert | — |
> > | lfdsss/Tee-es-t | main | 3c079bf (Robot: followup) | — | #? |
> >
> > ## Commits Tee-es-t en attente (locaux, non poussés)
> >
> > - 14c5df5
> > - - 130a61d
> >   - - 5827878
> >    
> >     - Point dur : ces commits vivent sur la machine locale. Le push doit être fait depuis l'agent CLI / Playwright local, pas depuis le navigateur. Une fois la branche poussée sur le remote, la PR sera ouverte côté navigateur.
> >    
> >     - ## Accès
> >    
> >     - - Compte navigateur courant : **LFDS31** (pas de Write direct sur `lfdsss/Tee-es-t`)
> > - Compte cible initialement prévu : **them311** (statut Write à confirmer)
> > - - Contournement actif : fork `LFDS31/Tee-es-t` synchronisé avec upstream, PR via fork → upstream
> >  
> >   - ## PR à surveiller
> >  
> >   - - #4 — CI vert (Vercel preview / Pre-merge validation), zéro review négative
> >     - - #8 — CI vert, zéro review négative
> >      
> >       - Aucune action de correction en attente. Réveil sur tout nouvel évènement (commit, review, échec CI).
> >      
> >       - ## Outils
> >      
> >       - - `/togo` : commande maître unique (fusion ex-`/togo` + ex-`/synchro`). Lit ce fichier au démarrage, le met à jour après chaque décision.
> > - Automatisation navigateur côté agent : Playwright MCP sur les 3 repos (navigate / click / fill / screenshot).
> > - - Côté humain : extension Chrome « Claude for Chrome » dans le navigateur perso, non embarquable dans un repo.
> >  
> >   - ## Dernière décision
> >  
> >   - Fork `LFDS31/Tee-es-t` créé et synchronisé avec `lfdsss/Tee-es-t:main`. SYNCHRO.md initialisé sur branche `chore/synchro-md` du fork, PR ouverte vers `lfdsss/Tee-es-t:main`.
> >  
> >   - ## Prochaine action
> >
> >   - Merge de la PR SYNCHRO.md (côté owner `lfdsss`), puis attente du push des 3 commits Tee-es-t locaux pour ouverture de la PR fonctionnelle.
> >   - 
