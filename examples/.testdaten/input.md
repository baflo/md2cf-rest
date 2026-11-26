> [!NOTE]
> 📋 Diese Seite ist mit einem Jira-Ticket verknüpft: [PFM-267316](https://jira.lvm.de/jira/browse/PFM-267316)
> 




## Planung

Soll ca. für die Rechtsschutzfreigabe, also zu #REL-2609 eingeplant werden


## Problembeschreibung

> Bei dem Partner Meyer in Tabarz (40007340) wird das Rahmenabkommen nicht im Schaden angezeigt. Es wurde aber ordnungsgemäß hinterlegt.
> Bei anderen Werkstätten werden im Schaden Rahmenabkommen angezeigt. In anderen Schäden fehlt bei Meyer das Rahmenabkommen...



## Ursache

Laut Marc Hugo tritt das Problem auf, wenn der Partner nur die Rolle "Autohauskooperation" hat, nicht aber "Werkstatt" bzw. "Reparatur". Hat es denn auch etwas mit "Kooperationswerkstatt" zu tun?

Laut Dr. Bernd Forsmann könnte die Rolle "Autohauskooperation" evtl. bei der Dunkelsuche nicht berücksichtigt werden, was den Fehler erklären würde.

Wenn `SchadenPartnerHelper#getFilterErgebnisRollen` hier genutzt wird, könnte das bedeuten, dass `Autohauskooperation` einfach (noch) nicht als `Partnerdienstleisterrolle` definiert ist und deswegen nicht als FilterRolle ermittelt wird.

offenbar hängt das ganze Problem daran, dass `SchadenPartnerHelper#getFilterErgebnisRollen` mit dem Parameter `oberrolle=true` aufgerufen wird, um die passenden Rollen für die **Erstsuche** zu finden. Aus "Gründen" ist diese automatische Ermittlung mit Oberrollen in diesem Kontext problemantisch und kann zu Fehlern führen.
- es wird eine **Erstsuchrolle** verwendet, um Dupletten durch Suche nach mehreren Rollen zu verhindern




## Fragen

Was sind Oberrollen?
- hängt mit "Rollenbündel" und dem "Rollenbaum" zusammen, den man auch in der Suche sieht

- allerdings hängt das nicht wirklich mit der Struktur in der Suche zusammen. Laut Dr. Bernd Forsmann gibt es auch keine Stelle, an der man es visuell sehen kann. Bernd möchte sich den Schuh nicht anziehen und tätigt die Aussage, **dass er unserer generische Lösung nicht unterstützen möchte.**



Warum sind sie hier problematisch?
- Bei verschiedenen Rollen in K gibt es mehrere Oberrollen
    - AHK-Werkstätten

    - SVs

    - Rechtsanwälte

    - ...


- wir haben ein generisches Konstrukt programmiert, welches nach Ober- und Unterrollen bei Partner suchen würde, um daraufhin gestaffelte Suchen durchzuführen???

- bei Partner ist aber das System mit Oberrollen nicht durchweg bekannt und wurde die letzten 6 Jahre nicht sauber gepflegt



## Lösung?

Die Rollen für die Erstsuche sollten hart hinterlegt werden. Da es mit den Beteiligten zusammenhängt, die im Rahmen der RS-Umsetzung massiv bearbeitet werden, soll dies zusammen mit Rechtsschutz im September 2026 raus gehen.

