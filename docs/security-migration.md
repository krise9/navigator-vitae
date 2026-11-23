# Persoonlijke toegang: migratie en testbewijs

Status: productieomschakeling en geschiedenisopschoning goedgekeurd door Kris op 23 november 2026; database-migratie inmiddels toegepast. Kris koos persoonlijke wachtwoorden voor de testfase omdat er geen eigen maildienst is. De huidige publieke app blijft kwetsbaar tot de gecontroleerde omschakeling is uitgevoerd.

## Wat verandert

- Supabase Auth met persoonlijke wachtwoorden, uitsluitend voor vooraf aangemaakte accounts. De app bevat geen registratieknop. Geen gedeeld adminwachtwoord en geen login met een Navigator-ID.
- Een beheerder koppelt ieder geverifieerd Auth-account expliciet aan één bestaand dossier via `participants.auth_user_id`. Geen automatische koppeling op basis van een zelf opgegeven ID of e-mailadres.
- `app_admins` bevat de bevoegde Auth-gebruikers. Alleen een databasebeheerder kan deze lijst wijzigen. Een appgebruiker kan alleen zijn eigen adminlidmaatschap lezen. Adminrechten worden bij iedere uitvoering opnieuw opgehaald, niet vertrouwd uit een widget of bewerkbare gebruikersmetadata.
- Eigenaar-RLS beschermt alle vier bestaande tabellen. Deelnemers lezen hun eigen actieve dossier en resultaten, admins lezen alle dossiers. Deelnemers mogen alleen eigen, consistent gekoppelde inzendingen toevoegen; geen bestaande rijen aanpassen of verwijderen. Accounts zonder koppeling zien geen dossiers. Inactieve dossiers zijn voor deelnemers ontoegankelijk.
- De app gebruikt uitsluitend een publishable/anon key, plus de persoonlijke JWT. Service-role/secret keys worden geweigerd. De oude `SUPABASE_KEY`-instelling wordt niet meer gebruikt.
- Iedere browsersessie krijgt een eigen Supabase-client. Uitloggen en mislukte/verlopen authenticatie wissen formulierdata en sessiestaat. Er is geen gedeelde clientcache.
- Ikigai wordt in één transactie opgeslagen. Unieke indexen blokkeren dubbele runs en dubbele antwoorden. Bestaande IDs en antwoorden blijven behouden.
- De publieke CSV-deelnemerslijst wordt uit de nieuwe code verwijderd. Dit verwijdert **geen eerdere Git-versies**, oude branches, forks of caches.

De deelnemersinterface toont nog steeds geen automatisch analyserapport. Een eigenaar kan zijn eigen opgeslagen gegevens wel via de beveiligde API lezen; de database behandelt deze niet als geheim voor de deelnemer zelf.

## Vastgesteld op 23 november 2026

Productieproject: `zmjhdcrmxuzbfexxxene`, PostgreSQL 17, ACTIVE_HEALTHY.
Publieke app: <https://navigator-vitae-beta.streamlit.app/>. Startpagina en ID-invoerscherm zijn bekeken, zonder echte antwoorden in te vullen. Hostinginstellingen, deployment-SHA en de gebruikte runtime-sleutel zijn niet ingezien.

| Gegevens | Aantal |
|---|---:|
| Deelnemers | 7 |
| Ikigai-runs | 4 |
| Ikigai-antwoorden | 80 |
| Gedragsprofielen | 6 |
| Auth-accounts | 0 |

Vier deelnemers hebben een e-mailadres ingevuld; drie niet. Dit bewijst niet dat de vier adressen juist of geverifieerd zijn. Geen dubbele run/deelnemer-versiecombinaties, dubbele vraag/runcombinaties of afwijkende Navigator-ID-koppelingen gevonden. RLS staat al aan, maar zonder policies. Geen functies in het publieke schema gevonden.

Na expliciet akkoord is een versleutelde lokale export van de vier gegevenstabellen gemaakt, buiten de repository. De export is ontsleuteld ter controle en bevat 7/4/80/6 records. Bestanden hebben alleen lees-/schrijfrechten voor de lokale gebruiker. Bewaar de herstelsleutel apart van de versleutelde export. Dit is een data-export, geen volledige Supabase/PITR-back-up; een herstel naar een echte Supabase-testomgeving is nog niet uitgevoerd. Geen persoonsgegevens of back-ups toevoegen aan deze PR.

## Voorbereiding vóór productieomschakeling

1. Maak een afzonderlijke Supabase-testomgeving met fictieve deelnemers. Pas daar eerst `db/proposed-auth.sql` toe. De SQL is getest met PostgreSQL via PGlite; dit vervangt geen echte GoTrue/PostgREST-integratietest.
2. Gebruik Email/password Auth; schakel publieke registratie en anonymous sign-in uit. Kies unieke wachtwoorden van minstens 16 tekens en passende Auth rate limits. Zonder SMTP zijn uitnodigingen, e-mailcodes en herstelmails niet beschikbaar. Wachtwoorden worden rechtstreeks en vertrouwelijk door de gebruiker ingesteld of individueel via een veilig kanaal overgedragen, nooit via GitHub. Een vergeten wachtwoord vraagt gecontroleerd beheerherstel. SMTP en e-mailcodes kunnen later worden toegevoegd.
3. Maak vooraf Auth-accounts voor gecontroleerde e-mailadressen. Een beheerder controleert de identiteit en het adres en maakt het account aan met Auto confirm. Dit is een beheerbeslissing, geen bewijs van mailboxbezit via een bevestigingsmail. Gebruik geen gedeelde wachtwoorden of fictieve adressen voor bestaande testers.
4. Koppel in de testomgeving twee fictieve deelnemers en een apart adminaccount. Test echte wachtwoordlogin, fout wachtwoord en verlopen sessie, twee gelijktijdige browsers, beide formulieren, heraanmelden, adminbeheer en directe API-toegang tot andermans IDs.
5. Leg de werkelijke productiebranch, Pythonversie, secrets-namen en het type bestaande API-sleutel vast zonder sleutelwaarden te publiceren. De nieuwe packages zijn vastgezet; gebruik Python 3.13 zoals lokaal getest.
6. Laat Kris de zeven koppelingen en het admin-e-mailadres bevestigen. Ontbrekende adressen blijven ongekoppeld en dus geblokkeerd; er wordt niemand op basis van een geraden ID toegelaten.

De lokale Supabase CLI werd door het besturingssysteem beëindigd (SIGKILL). Daarom is `db/proposed-auth.sql` een expliciet te beoordelen SQL-voorstel, geen verzonnen CLI-migratiebestand en geen toegepaste migratie. Neem het bij de rollout op in de officiële migratiehistoriek met de dan werkende CLI/tooling.

## Goedgekeurde omschakeling (eerst echte login controleren)

1. Plan een onderhoudsmoment. Stop toegang tot de oude Streamlit-app en sluit oude workers/sessies. Voorkom gelijktijdig schrijven vanuit oude code.
2. Maak een nieuwe versleutelde back-up en controleer de actuele aantallen, relaties en unieke waarden opnieuw. De aantallen hierboven zijn een momentopname; nieuw legitiem werk mag niet worden overschreven.
3. Voer `db/proposed-auth.sql` als één transactie uit. Bij bestaande onverwachte policies of conflicterende data stopt de migratie. Los zo'n conflict op zonder gegevens te verwijderen. Controleer na afloop RLS, grants en Supabase Security Advisor.
4. Configureer productie-Auth zoals in de testomgeving; SMTP blijft uit in deze testfase. Maak de zeven persoonlijke accounts en het adminaccount aan. Voer de bevestigde koppelingen in een transactie uit, met parameters via een beheerverbinding (nooit in publieke Git-bestanden):

   ```sql
   update public.participants set auth_user_id = :verified_auth_user_uuid
   where id = :existing_participant_uuid and auth_user_id is null;
   -- Verwacht precies één gewijzigde rij per bevestigde koppeling.
   insert into public.app_admins(user_id) values (:verified_admin_auth_uuid);
   ```

5. Deploy de gereviewde PR. Stel alleen `SUPABASE_URL` en `SUPABASE_PUBLISHABLE_KEY` in. Verwijder de oude `SUPABASE_KEY` uit de hostingconfiguratie. Publiceer nooit echte secrets in GitHub of een screenshot.
6. Identificeer en trek de oude bevoorrechte sleutel in of roteer hem, zodat een oude deployment niet kan blijven werken. Een legacy service-role key kan onderdeel zijn van gedeelde JWT-sleutels: inventariseer eerst andere gebruikers en keur de impact goed. Alleen een sleutel uit Streamlit verwijderen trekt die sleutel niet in.
7. Controleer echte login, beide formulieren met uitsluitend testaccounts, afmelden, een ongekoppeld account en adminbeheer. Controleer dat alleen een Navigator-ID en de oude admincode nergens toegang geven. Controleer opnieuw de historische 7/4/80/6 records en inhoudshashes; houd nieuwe testrecords apart.
8. Hervat toegang pas na deze controles. Deelnemers melden zich voortaan aan met hun eigen e-mailadres en persoonlijke wachtwoord. Hun bestaande dossier, deelnamehistoriek en resultaten blijven bestaan.

Een uitgelogde Supabase access token kan tot zijn vervaldatum geldig blijven; sign-out trekt refresh tokens in. Zet de JWT-levensduur daarom kort. Intrekken van een dossierkoppeling, pauzeren van een deelnemer of verwijderen van adminlidmaatschap werkt voor RLS direct, ook bij een nog geldige JWT.

## Publieke Git-historiek

De CSV en oude admincode blijven in de bestaande publieke geschiedenis staan totdat die is opgeschoond. De oude code wordt door de nieuwe app nergens meer gecontroleerd; wijzig eventuele andere plaatsen waar hetzelfde wachtwoord is hergebruikt. De codehistoriek verwijderen vervangt het ongeldig maken van toegang niet.

Kris heeft historieherschrijving expliciet goedgekeurd: bewaar eerst een afgeschermde Git-back-up, verwijder `data/registry.csv` en het historische `responses.csv` uit alle relevante refs en vervang de oude credential in historische blobs, controleer het resultaat en force-push alleen de afgesproken refs. Medewerkers moeten daarna opnieuw clonen. Vraag GitHub zo nodig om gecachte commit-/PR-weergaven te verwijderen. Maak de repository tijdelijk privé zolang publiek toegankelijke historische deelnemersgegevens niet afgeschermd zijn; dit vereist repositorybeheerrechten. Kopieën en forks kunnen niet gegarandeerd worden teruggehaald.

## Testbewijs

Uitgevoerd, zonder productie te wijzigen:

- `python -m pytest tests -q`: 10 tests geslaagd. Streamlit: wachtwoordlogin, weigering onjuist wachtwoord, oud sessiestaat/ID geeft geen toegang, 20 Ikigai-antwoorden opslaan, volledige MBTI-vragenlijst opslaan, uitloggen wist data, verlopen sessie, adminlidmaatschap, ongekoppeld account en geweigerde privileged keys. Auth-transport is hierbij gesimuleerd.
- De echte Supabase Python SDK is met gesimuleerde HTTP-responses getest: gebruikers-JWT gaat naar PostgREST, twee clients delen geen login, logout verwijdert de clienttoken.
- `npm run test:rls`: 36 controles geslaagd met echte PostgreSQL-semantiek via PGlite, fictieve data. Aantallen 7/4/80/6 blijven gelijk bij migratie; anoniem/ongekoppeld ziet niets; eigenaar ziet alleen zichzelf; admin ziet alle dossiers; escalatie, lezen/schrijven voor anderen, ID-verwisseling, wijzigen/verwijderen en dubbels worden geblokkeerd; een fout tijdens het opslaan draait de volledige Ikigai-inzending terug; intrekking admin/actieve status werkt.
- Pythonbestanden compileren. Geen sleutelpatronen gevonden in de onderzochte actuele tekstbestanden. Dit is geen garantie dat er nooit secrets in historische commits hebben gestaan.

Nog niet uitgevoerd: echte Supabase wachtwoord-Auth en PostgREST-end-to-end, stagingdeployment, productieconfiguratie, accountkoppeling, sleutelrotatie, productie-deployment, opschoning Git-historiek en hersteltest van de echte back-up in Supabase. Productie blijft onveranderd tot de vereiste echte inlogcontrole is geslaagd.

## Terugval

Laat bij een fout de app in onderhoud. Herstel de applicatie met een gecorrigeerde beveiligde versie; zet nooit de oude ID-only toegang terug aan. De migratie verwijdert geen bestaande data, dus de nieuwe kolom/tabellen/policies kunnen blijven staan terwijl de fout wordt opgelost. Een dataherstel is alleen een laatste redmiddel, na vergelijking van actuele data met de back-up en afzonderlijk akkoord; overschrijf geen nieuw werk.

Referenties: [Supabase OTP](https://supabase.com/docs/guides/auth/auth-email-passwordless), [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), [API keys](https://supabase.com/docs/guides/api/api-keys).

## Uitvoering op 23 november 2026

- Persoonlijke wachtwoordlogin door de eigenaar succesvol getest tegen echte Supabase Auth.
- Beheeraccount via de Supabase-interface door de eigenaar aangemaakt; wachtwoord is niet door de agent opgehaald of opgeslagen.
- Publieke registratie uitgezet; anonymous sign-in stond al uit. Geen SMTP ingesteld.
- Migratie `individual_password_auth_owner_rls` toegepast. Beheerrechten expliciet gekoppeld.
- Toegang van `service_role` tot alle dossier- en beheertabellen ingetrokken: een oude bevoorrechte app kan deze gegevens niet meer benaderen. Dit is aanvullende afscherming; de oude projectsleutel zelf wordt hiermee niet ingetrokken.
- De volledige inhoudshashes van de vier bestaande tabellen komen na migratie overeen met vóór de migratie (nieuwe lege eigenaarskolom buiten vergelijking). Aantallen blijven 7/4/80/6.
- Echte Supabase/RLS-controles geslaagd voor admin en ongekoppeld account. De persoonlijke gebruikerssessie heeft via de echte PostgREST-verbinding de beheerweergave bereikt.
- De zeven bestaande deelnemers zijn nog niet aan Auth-accounts gekoppeld. Koppel pas na verificatie van identiteit en persoonlijke accountgegevens; geen automatische e-mailmatching.
- Websiteomschakeling en publicatie van opgeschoonde geschiedenis volgen na deze controle. Dit uitvoeringsverslag heeft voorrang op de eerdere voorbereidende statusbeschrijvingen.
