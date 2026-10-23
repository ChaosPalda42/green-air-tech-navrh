<?php
/* JSON, který se vkládá přímo do stránky (window.GAT_* a bloky
   <script type="application/json">).

   Prohlížeč ukončí <script> na prvním `</script` v jeho obsahu — i když je
   uvnitř řetězce. Text uložený v administraci by tak stránku rozsekl, proto
   se `</`, `<!--` a `-->` zapíšou tak, aby je parser HTML nepoznal. Pro
   JavaScript je to pořád tentýž řetězec: `<\/` je v JSONu obyčejné lomítko
   a `<` je `<`.

   Ve výchozím obsahu webu žádná z těch posloupností není (jediná značka
   v textech je <br>), takže vykreslení ukázky zůstává bajt po bajtu stejné. */

declare(strict_types=1);

namespace App\Jadro;

final class Json
{
    public static function doSkriptu(mixed $data): string
    {
        $json = json_encode(
            $data,
            JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR
        );

        return str_replace(
            ['</', '<!--', '-->'],
            ['<\\/', '\\u003C!--', '--\\u003E'],
            $json
        );
    }
}
