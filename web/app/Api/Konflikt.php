<?php
/* Požadavek nejde splnit, protože by si rozporoval s tím, co v datech už je —
   typicky obsazený e-mail. Není to chyba serveru: Router z toho dělá 409 a
   administrace to umí říct člověku. Rozbitá databáze tudy nejde, ta má
   spadnout nahlas. */

declare(strict_types=1);

namespace App\Api;

final class Konflikt extends \RuntimeException
{
}
