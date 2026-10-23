<?php
/* Zámek administrace při hádání hesla: rozhoduje, jestli je přihlášení
   kvůli opakovaně špatným heslům zamčené a kolik sekund do odemčení zbývá.
   Čisté rozhodování bez stavu — časy pokusů přicházejí zvenčí
   (tabulka `udalosti`), nic se nepíše, nic se nečte ze sítě.

   Počítá se ve dvou nezávislých sadách: pokusy z jedné adresy (na kohokoli)
   a pokusy na jeden účet (odkudkoli). Adresu zamyká desátý pokus, účet
   teprve třicátý — účet je záchranná síť proti hádání z mnoha adres, ne
   vypínač na správce. Čeká se to delší z obou sad. */

declare(strict_types=1);

namespace App\Auth;

final class Zamek
{
    public const OKNO = 900;          // kolik sekund dozadu se špatné pokusy počítají
    public const LIMIT_ADRESA = 10;   // kolikátý špatný pokus z JEDNÉ ADRESY zamkne
    public const LIMIT_UCET = 30;     // kolikátý špatný pokus na JEDEN ÚČET zamkne

    /**
     * Je přihlášení zamčené? Zamkne, když zamyká aspoň jedna ze sad:
     * pokusy z adresy návštěvníka (na kohokoli) nebo pokusy na ten účet
     * (odkudkoli). V okně (ted - OKNO, ted] se počítají i pokusy s časem
     * v budoucnosti (rozejité hodiny serveru). Pořadí vstupu je jedno.
     */
    public static function zamceno(array $zAdresy, array $uctu, int $ted): bool
    {
        return self::ceka($zAdresy, $uctu, $ted) > 0;
    }

    /**
     * Kolik sekund zbývá do odemčení — to DELŠÍ z obou sad; 0, když
     * zamčeno není. Zámek drží do chvíle, kdy z okna vypadne LIMIT-tý
     * nejnovější pokus dané sady.
     */
    public static function ceka(array $zAdresy, array $uctu, int $ted): int
    {
        return max(
            self::cekaSada($zAdresy, self::LIMIT_ADRESA, $ted),
            self::cekaSada($uctu, self::LIMIT_UCET, $ted),
        );
    }

    /**
     * Čekání jedné sady: 0, když v okně není aspoň $limit pokusů, jinak
     * do okamžiku, kdy z okna vypadne $limit-tý nejnovější pokus.
     */
    private static function cekaSada(array $casy, int $limit, int $ted): int
    {
        $vOkne = [];
        foreach ($casy as $cas) {
            if ($cas > $ted - self::OKNO) {
                $vOkne[] = $cas;
            }
        }
        if (count($vOkne) < $limit) {
            return 0;
        }
        rsort($vOkne);
        $klicovy = $vOkne[$limit - 1];
        return max(0, $klicovy + self::OKNO - $ted);
    }
}
