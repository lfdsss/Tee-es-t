# Glossaire complet de la securite des cartes SIM

Guide de reference sur toutes les techniques, attaques et termes lies a la securite et au piratage des cartes SIM.

---

## 1. SIM Swapping (Echange de SIM)

**Definition :** Technique de fraude ou un attaquant convainc un operateur telephonique de transferer le numero de telephone de la victime vers une nouvelle carte SIM controlee par l'attaquant.

**Comment ca marche :**
- L'attaquant collecte des informations personnelles sur la victime (ingenierie sociale, fuites de donnees, phishing).
- Il contacte l'operateur en se faisant passer pour la victime.
- Il demande le transfert du numero vers une nouvelle SIM.
- Une fois le transfert effectue, l'attaquant recoit tous les appels et SMS de la victime.

**Consequences :**
- Contournement de l'authentification a deux facteurs (2FA) par SMS
- Acces aux comptes bancaires, email, reseaux sociaux
- Vol d'identite complet
- Vol de cryptomonnaies

**Comment se proteger :**
- Utiliser une application d'authentification (Google Authenticator, Authy) plutot que le SMS
- Mettre un code PIN/mot de passe aupres de son operateur
- Ne pas partager d'informations personnelles en ligne
- Activer les alertes de changement de SIM

---

## 2. SIM Cloning (Clonage de SIM)

**Definition :** Processus de duplication des donnees d'une carte SIM vers une autre carte, creant ainsi une copie identique.

**Comment ca marche :**
- Extraction des cles d'authentification (Ki) stockees sur la SIM originale
- Utilisation d'un lecteur de carte SIM et d'un logiciel specialise
- Copie des donnees IMSI et Ki sur une carte SIM vierge programmable

**Termes techniques associes :**
- **Ki (Authentication Key)** : Cle secrete de 128 bits stockee sur la SIM, utilisee pour l'authentification sur le reseau
- **IMSI (International Mobile Subscriber Identity)** : Identifiant unique de l'abonne stocke sur la SIM
- **ICCID (Integrated Circuit Card Identifier)** : Numero de serie unique de la carte SIM physique

**Consequences :**
- Deux telephones partagent le meme numero
- Interception des appels et SMS
- Utilisation frauduleuse du forfait de la victime

---

## 3. SIM Jacking (Simjacker)

**Definition :** Attaque exploitant une vulnerabilite dans le logiciel S@T Browser (SIMalliance Toolbox Browser) integre dans certaines cartes SIM.

**Comment ca marche :**
- L'attaquant envoie un SMS specialement forge contenant des commandes S@T Browser
- La carte SIM execute ces commandes sans interaction de l'utilisateur
- Le telephone ne montre aucune notification du SMS recu

**Capacites de l'attaque :**
- Recuperer la localisation GPS du telephone
- Obtenir le numero IMEI de l'appareil
- Forcer le telephone a passer des appels
- Envoyer des SMS depuis le telephone de la victime
- Ouvrir un navigateur vers une URL malveillante
- Desactiver la carte SIM

**Impact :** Plus d'un milliard de telephones etaient potentiellement vulnerables lors de la decouverte en 2019.

---

## 4. SIM Ping (Ping de SIM)

**Definition :** Technique consistant a envoyer un signal silencieux (silent SMS / stealth ping) a un numero de telephone pour verifier si la carte SIM est active et localiser l'appareil.

**Comment ca marche :**
- Envoi d'un SMS de type 0 (silent SMS) ou d'un ping reseau
- Le telephone recoit le signal mais n'affiche aucune notification
- La reponse du reseau confirme que le numero est actif
- Les donnees de triangulation des antennes-relais permettent de localiser l'appareil

**Types de ping :**
- **Silent SMS (SMS de type 0)** : Message invisible qui force le telephone a repondre au reseau
- **Ping IMSI** : Requete directe au reseau pour localiser un IMSI specifique
- **HLR Lookup (Home Location Register)** : Interrogation de la base de donnees de l'operateur pour obtenir le statut d'un numero

**Utilisation :**
- Forces de l'ordre pour la localisation de suspects
- Surveillance et espionnage
- Verification de l'activite d'un numero avant une attaque

---

## 5. IMSI Catcher (Stingray)

**Definition :** Dispositif qui se fait passer pour une antenne-relais legitime (fausse station de base) pour intercepter les communications mobiles.

**Noms courants :** Stingray, Cell-site Simulator, Fake Base Station, Dirtbox

**Comment ca marche :**
- L'appareil emet un signal plus fort que les antennes environnantes
- Les telephones a proximite se connectent automatiquement a la fausse antenne
- Toutes les communications transitent par le dispositif avant d'etre relayees

**Capacites :**
- Capturer les numeros IMSI et IMEI de tous les telephones a proximite
- Intercepter les appels et SMS non chiffres
- Suivre les deplacements des appareils
- Forcer un downgrade de 4G/5G vers 2G (moins securise)
- Injecter des SMS ou des appels

**Protection :**
- Utiliser des applications de communication chiffrees (Signal, WhatsApp)
- Applications de detection d'IMSI Catchers (AIMSICD, SnoopSnitch)

---

## 6. SIM Farming

**Definition :** Utilisation massive de nombreuses cartes SIM simultanement via des dispositifs multi-SIM (SIM banks/SIM farms) pour des activites frauduleuses.

**Usages malveillants :**
- Envoi massif de spam par SMS
- Creation en masse de faux comptes sur les reseaux sociaux
- Fraude aux verifications par SMS
- Arnaque telephonique a grande echelle
- Manipulation de votes ou de sondages en ligne

**Equipement :**
- **SIM Bank** : Dispositif pouvant accueillir des dizaines a des centaines de cartes SIM
- **Passerelle GSM (GSM Gateway)** : Boitier permettant de router les appels via des cartes SIM
- **SIM Server** : Serveur gerant les cartes SIM a distance

---

## 7. SIM Sniffing (Ecoute SIM)

**Definition :** Interception des communications entre la carte SIM et le reseau mobile en capturant les signaux radio.

**Comment ca marche :**
- Utilisation de recepteurs SDR (Software Defined Radio) pour capturer les signaux GSM
- Decodage des trames de communication
- Exploitation des faiblesses du chiffrement A5/1 (GSM 2G)

**Protocoles vulnerables :**
- **A5/0** : Pas de chiffrement (le plus vulnerable)
- **A5/1** : Chiffrement GSM standard (casse depuis 2009)
- **A5/2** : Version affaiblie de A5/1 (trivialement cassable)
- **A5/3 (KASUMI)** : Utilise en 3G, plus robuste mais avec des faiblesses connues

---

## 8. SS7 Attack (Attaque sur le protocole SS7)

**Definition :** Exploitation des vulnerabilites du protocole SS7 (Signaling System 7), le protocole utilise par les operateurs pour gerer les appels et SMS entre reseaux.

**Capacites :**
- Intercepter les appels et SMS de n'importe quel numero dans le monde
- Localiser un telephone en temps reel
- Rediriger les appels et SMS vers un autre numero
- Ecouter les conversations en cours
- Lire les SMS (y compris les codes 2FA)

**Pourquoi c'est possible :**
- SS7 a ete concu dans les annees 1970 sans mecanisme de securite
- Tout operateur connecte au reseau SS7 peut envoyer des requetes
- Des centaines d'operateurs dans le monde ont acces au reseau SS7
- Le protocole fait confiance a toutes les requetes sans verification

---

## 9. SIM Toolkit (STK) Attacks

**Definition :** Exploitation des applications SIM Toolkit integrees dans la carte SIM pour executer des commandes malveillantes.

**Le SIM Toolkit permet :**
- Afficher des menus sur le telephone
- Envoyer des SMS
- Initier des appels
- Lancer le navigateur
- Acceder a la localisation

**Vecteurs d'attaque :**
- OTA (Over-The-Air) updates malveillantes envoyees par SMS binaires
- Exploitation de failles dans les applets Java Card de la SIM
- Injection de commandes via des messages SMS specialement forges

---

## 10. eSIM Hijacking (Detournement d'eSIM)

**Definition :** Version moderne du SIM Swapping adaptee aux eSIM (SIM electroniques integrees).

**Comment ca marche :**
- L'attaquant obtient acces au compte de l'operateur de la victime
- Il genere un nouveau QR code d'activation eSIM
- Il active l'eSIM sur son propre appareil
- Le profil eSIM de la victime est desactive

**Specificites :**
- Plus rapide que le SIM Swapping traditionnel (pas besoin de SIM physique)
- Peut etre realise entierement a distance
- Certains operateurs ont des processus de verification faibles pour les transferts eSIM

---

## 11. SIM Port-Out Scam (Arnaque au portage)

**Definition :** Variante du SIM Swapping ou l'attaquant initie un transfert (portabilite) du numero vers un autre operateur.

**Difference avec le SIM Swapping :**
- Le SIM Swapping reste chez le meme operateur
- Le Port-Out transfere le numero vers un autre operateur
- Plus difficile a detecter et a inverser car deux operateurs sont impliques

---

## 12. Termes techniques essentiels

### Identifiants et cles

| Terme | Signification | Role |
|-------|---------------|------|
| **IMSI** | International Mobile Subscriber Identity | Identifiant unique de l'abonne (15 chiffres) |
| **IMEI** | International Mobile Equipment Identity | Identifiant unique de l'appareil (15 chiffres) |
| **Ki** | Authentication Key | Cle secrete pour l'authentification reseau |
| **ICCID** | Integrated Circuit Card ID | Numero de serie de la carte SIM |
| **MSISDN** | Mobile Station ISDN Number | Le numero de telephone |
| **TMSI** | Temporary Mobile Subscriber Identity | Identite temporaire pour proteger l'IMSI |
| **LAI** | Location Area Identity | Identifiant de la zone de localisation |
| **RAND** | Random Number | Nombre aleatoire utilise dans l'authentification |
| **SRES** | Signed Response | Reponse d'authentification calculee avec Ki et RAND |
| **Kc** | Ciphering Key | Cle de chiffrement derivee pour la session |

### Composants reseau

| Terme | Signification | Role |
|-------|---------------|------|
| **HLR** | Home Location Register | Base de donnees principale des abonnes |
| **VLR** | Visitor Location Register | Base de donnees des abonnes en itinerance |
| **AuC** | Authentication Center | Centre d'authentification |
| **MSC** | Mobile Switching Center | Commutateur du reseau mobile |
| **BSC** | Base Station Controller | Controleur des stations de base |
| **BTS** | Base Transceiver Station | Antenne-relais |

---

## 13. WIB Attack (Wireless Internet Browser)

**Definition :** Similaire au Simjacker, cette attaque exploite le navigateur WIB (Wireless Internet Browser) present sur certaines cartes SIM.

**Capacites identiques au Simjacker :**
- Localisation de l'appareil
- Envoi de SMS
- Lancement d'appels
- Ouverture de navigateur
- Tout cela sans aucune interaction de l'utilisateur

---

## 14. OTA (Over-The-Air) Attacks

**Definition :** Attaques exploitant le mecanisme de mise a jour a distance des cartes SIM.

**Comment ca marche :**
- Les operateurs utilisent des SMS binaires OTA pour mettre a jour les cartes SIM
- Si les cles de chiffrement OTA sont faibles (DES au lieu de 3DES/AES), un attaquant peut forger de fausses mises a jour
- L'attaquant peut installer des applets malveillantes sur la SIM

**Decouverte :** Karsten Nohl a demontre cette vulnerabilite en 2013 lors de la conference Black Hat.

---

## 15. SIM Card Data Extraction

**Definition :** Techniques d'extraction des donnees stockees sur une carte SIM.

**Donnees recuperables :**
- Repertoire telephonique (ADN - Abbreviated Dialing Numbers)
- SMS stockes sur la SIM
- Derniers numeros appeles (LND - Last Number Dialed)
- IMSI et ICCID
- Informations de localisation (LOCI)
- Fichiers supprimes potentiellement recuperables

**Outils utilises :**
- Lecteurs de cartes SIM forensiques
- Logiciels : SIMSpy, MOBILedit, Cellebrite, Oxygen Forensics

---

## 16. Diameter Attack (Successeur de SS7)

**Definition :** Attaque similaire a SS7 mais sur le protocole Diameter utilise dans les reseaux 4G/LTE.

**Vulnerabilites :**
- Localisation des abonnes
- Interception de donnees
- Deni de service
- Fraude a l'itinerance

---

## 17. GTP (GPRS Tunnelling Protocol) Attacks

**Definition :** Attaques ciblant le protocole GTP utilise pour le transport de donnees dans les reseaux mobiles.

**Risques :**
- Usurpation d'identite d'abonne
- Interception du trafic de donnees
- Fraude au trafic
- Deni de service sur le reseau

---

## 18. Mesures de protection recommandees

### Pour les utilisateurs
1. **Ne jamais utiliser le SMS comme seul facteur d'authentification** - Privilegier les applications TOTP ou les cles de securite physiques (YubiKey)
2. **Definir un code PIN SIM** - Empeche l'utilisation de la SIM dans un autre appareil
3. **Contacter son operateur** pour ajouter un mot de passe supplementaire sur le compte
4. **Limiter les informations personnelles** partagees en ligne
5. **Surveiller les signes d'attaque** : perte soudaine de signal, impossibilite de passer des appels
6. **Activer les notifications** de changement de SIM aupres de l'operateur
7. **Utiliser une eSIM** avec une authentification forte si disponible

### Pour les operateurs
1. Implementer des verifications d'identite renforcees pour les changements de SIM
2. Utiliser le chiffrement AES pour les mises a jour OTA
3. Deployer des firewalls SS7/Diameter
4. Mettre en place des systemes de detection d'anomalies
5. Envoyer des alertes en temps reel aux clients lors de modifications de compte

---

## 19. Cadre legal

La plupart de ces techniques sont **illegales** lorsqu'elles sont utilisees sans autorisation :

- **SIM Swapping** : Usurpation d'identite, fraude, acces non autorise a des systemes informatiques
- **IMSI Catching** : Interception illegale de communications (sauf forces de l'ordre avec mandat)
- **SS7 Exploitation** : Violation des lois sur les telecommunications
- **SIM Cloning** : Contrefacon et fraude

Les peines peuvent inclure plusieurs annees de prison et des amendes importantes selon les juridictions.

---

*Ce document est fourni a des fins educatives et de sensibilisation a la securite. La connaissance de ces techniques est essentielle pour se proteger contre les menaces ciblant les communications mobiles.*
