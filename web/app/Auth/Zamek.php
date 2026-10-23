<?php
/* Zámek administrace při hádání hesla: rozhoduje, jestli je účet kvůli
   opakovaně špatným heslům zamčený a kolik sekund do odemčení zbývá.
   Čisté rozhodování bez stavu — časy pokusů přicházejí zvenčí
   (tabulka `udalosti`), nic se nepíše, nic se nečte ze sítě. */

declare(strict_types=1);

namespace App\Auth;

final class Zamek
{
    public const OKNO = 900;   // kolik sekund dozadu se špatné pokusy počítají
    public const LIMIT = 10;   // kolikátý špatný pokus v okně zamkne

    /**
     * Je účet zamčený? V okně [ted - OKNO, ted] se počítají i pokusy
     * s časem v budoucnosti (rozejité hodiny serveru). Pořadí vstupu je jedno.
     */
    public static function zamceno(array $casy, int $ted): bool
    {
        return self::ceka($casy, $ted) > 0;
    }

    /**
     * Kolik sekund zbývá do odemčení; 0, když zamčeno není.
     * Zámek drží do chvíle, kdy z okna vypadne LIMIT-tý nejnovější pokus.
     */
    public static function ceka(array $casy, int $ted): int
    {
        $vOkne = [];
        foreach ($casy as $cas) {
            if ($cas > $ted - self::OKNO) {
                $vOkne[] = $cas;
            }
        }
        if (count($vOkne) < self::LIMIT) {
            return 0;
        }
        // Zámek drží, dokud v okně zůstává aspoň LIMIT pokusů; odemkne se
        // v okamžiku, kdy z okna vypadne LIMIT-tý nejnovější pokus.
        rsort($vOkne);
        $klicovy = $vOkne[self::LIMIT - 1];
        return max(0, $klicovy + self::OKNO - $ted);
    }
}
