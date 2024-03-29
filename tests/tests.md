# Tests list

* Record `001  000000001` : no error
* Record n°2 :
  * No `001` or `035` : error `NO_RECORD_ID` (should also trigger `MISSING_MANDATORY_FIELD`)
* Record n°3 :
  * No `001`,  `035` without `$a` : error `NO_RECORD_ID` (should also trigger `MISSING_MANDATORY_FIELD`)
* Record `035 $a(OCoLC)0000000010` : no error on the ID retrieval (should also trigger `MISSING_MANDATORY_FIELD`)
* Record `001  000000100` :
  * `040` with `$g` : error `UNMAPPED_SUBFIELD`
  * `050` : error `UNMAPPED_FIELD`
  * `106 $a` is empty : error `EMPTY_SUBFIELD`
  * `205 $a` is only whitespaces : error `SUBFIELD_CONTENT_IS_ONLY_WHITESPACE`
  * `320` without subfields : error `DATAFIELD_WITHOUT_SUBFIELD`
* Record `035  $a(OCoLC)0000000101` :
  * No `001` : error `MISSING_MANDATORY_FIELD` (should also trigger `MISSING_FIELD_WITH_MANDATORY_SUBFIELD` for `$a`)
  * No `100` : error `MISSING_MANDATORY_FIELD` (should also trigger `MISSING_FIELD_WITH_MANDATORY_SUBFIELD` for `$a`)
  * No `200` : error `MISSING_MANDATORY_FIELD` (should also trigger `MISSING_FIELD_WITH_MANDATORY_SUBFIELD` for `$a`)
  * No `801` : error `MISSING_MANDATORY_FIELD`
  * No `099 $t` : error `MISSING_MANDATORY_SUBFIELD`
  * No `101` : error `MISSING_FIELD_WITH_MANDATORY_SUBFIELD`
  * No `995` : 4 error `MISSING_FIELD_WITH_MANDATORY_SUBFIELD`
* Record `001  000001000` :
  * `100` without `$a` : error `MISSING_MANDATORY_SUBFIELD`
  * `101` without `$a` : error `MISSING_MANDATORY_SUBFIELD`
  * `200` without `$a` : error `MISSING_MANDATORY_SUBFIELD`
  * `995` without `$b`, `$c`, `o`, `r` : 4 errors `MISSING_MANDATORY_SUBFIELD`
* Record `001  000001001` :
  * 2 `110` : error `NON_REPEATABLE_FIELD`
  * 2 `200` : error `NON_REPEATABLE_FIELD`
  * `010` with multiple `$a` : error `NON_REPEATABLE_SUBFIELD`
  * `701` with multiple `$a` : error `NON_REPEATABLE_SUBFIELD`
* Record `001  100000000` :
  * No `181` : no error
  * No `182` : no error
  * No `183` : no error
  * No `606` : no error
  * No `615` : no error
  * No `971` : no error
  * No `972` : no error
* Record `001  100000001` :
  * `181` without `$2` and `$c` : no error
  * `182` without `$2` and `$c` : no error
  * `183` without `$2` and `$a` : no error
  * `606` without `$2` : no error
  * `615` without `$2` : no error
  * `971` without `$9` : no error
  * `972` without `$9` : no error
* Record `001  110000000` :
  * `100 $a` pos 8 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 17 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 18 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 19 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 20 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 21 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 22-24 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 25 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 26-27 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 28-29 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 30-31 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 32-33 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `100 $a` pos 34-35 is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `181 $2` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `181 $c` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `182 $2` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `182 $c` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `183 $2` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `183 $a` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `606 $2` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `615 $2` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `971 $9` is invalid : error `ILLEGAL_CONTROLED_VALUE`
  * `972 $9` is invalid : error `ILLEGAL_CONTROLED_VALUE`
* Record `001  110000001` :
  * `099 $x` is invalid : error `ILLEGAL_AUTHORIZED_VALUE`
  * `099 $y` is invalid : error `ILLEGAL_AUTHORIZED_VALUE`
  * `101 $a` is invalid : error `ILLEGAL_AUTHORIZED_VALUE`
  * `102 $a` is invalid : error `ILLEGAL_AUTHORIZED_VALUE`
  * `995 $b` is invalid : error `ILLEGAL_AUTHORIZED_VALUE`
  * `995 $r` is invalid : error `ILLEGAL_AUTHORIZED_VALUE`
    