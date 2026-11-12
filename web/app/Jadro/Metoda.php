<?php
/* Skutečná metoda požadavku.

   Hosting u klienta (a řada dalších) PUT ani DELETE nepustí: Apache je
   odmítne 403 dřív, než se PHP vůbec spustí, takže by administrace
   neuložila vůbec nic. Prohlížeč proto pošle POST a skutečnou metodu
   připíše do hlavičky `X-HTTP-Method-Override`.

   Bere se JEN hlavička a JEN u POSTu. Hlavičku cizí stránka nenastaví
   (prohlížeč by si napřed vyžádal CORS preflight), kdežto formulář s polem
   `_method` jde odeslat odkudkoli — a tím by se obešlo, že mazání a zápis
   mají vlastní metodu. Tělo ani dotaz se proto nečtou. */

declare(strict_types=1);

namespace App\Jadro;

final class Metoda
{
    /** Metody, které si smí POST vyžádat hlavičkou. */
    public const DOVOLENE = ['PUT', 'DELETE'];

    /** @param array<string, mixed> $server obvykle $_SERVER */
    public static function skutecna(string $metoda, array $server): string
    {
        $metoda = strtoupper(trim($metoda));
        if ($metoda !== 'POST') {
            return $metoda;
        }

        $zadana = strtoupper(trim((string) ($server['HTTP_X_HTTP_METHOD_OVERRIDE'] ?? '')));

        return in_array($zadana, self::DOVOLENE, true) ? $zadana : 'POST';
    }
}
