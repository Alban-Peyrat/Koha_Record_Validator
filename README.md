# Record validator using KOHA's MARC framework and other

[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)

This application uses a CSV export of Koha MARC framework to check if :

* Unmapped fields & subfields are not present
* Mandatory fields & subfields are present
* Non repeatable fields & subfields are not repeated
* Authorized values limited subfields have legal values

__Developped with `pymarc 4.2.2.`__, might not work with version `5` of the library.

# Setting up

You need to export from Koha :

* The default MARC framework as a CSV file
* All authorised values (or only those who could be used) __adding branches and itemtypes to them__, the order of column __must be__ : `category`, `authorised_value`, `lib`, `lib_opac`

``` SQL
/* Example, remove the WHERE if you want to export every authorised value */
/* /!\ COLUMNS MUST FOLLOW THIS ORDER : category, authorised_value, lib, lib_opac */
SELECT category, authorised_value, lib, lib_opac
FROM authorised_values

UNION ALL 
SELECT "branches" AS category, branchcode AS "authorised_value", branchname as "lib", branchname as "lib_opac"
FROM branches

UNION ALL 
SELECT "itemtypes" AS category, itemtype AS "authorised_value", description as "lib", description as "lib_opac"
FROM itemtypes
```

Then you need to set up the following environment variables :

* `RECORDS_FILE` : full path to the file contining all the records to analyse
* `ERRORS_FILE`: full path to the file with errors (will be created / rewrite existing one)
* `KOHA_MARC_FRAMEWORK_FILE` : full path to the MARC framework file
* `KOHA_AUTH_VAL_FILE` : full path to the authorised values export file
* `CONTROL_VALUES_FILE` : full path to the control values XML file

[A default control values XML is provided](./controled_values.xml) _(do note that it's ArchiRès' one)_, the root must be `fields`, then it should always follow these conditions :

* `fields` root :
  * Does not use any attributes
  * Contains `field` nodes
* `field` nodes :
  * Must have an attribute `tag` (use `000` for the record label / leader)
  * Contains `subfield` nodes
* `subfield` nodes :
  * Must have an attribute `code` (use `@` for controlfields and the record label / leader)
  * Can have attribute `startPosition` and / or `endPosition` :
    * Position starts at `0`
    * Must contain only numbers (not even spaces)
    * Using only a start position means taking __only__ the character at this position
    * Using only end position does __nothing__
    * Using both position takes all characters __included__ in this interval (`0` - `2` will be characters `0`, `1` and `2`)
  * Contains `value` nodes
* `value` nodes :
  * Must have an attribute `value`
  * Can have an attribute `name` (if name is not used, `value` will be used instead as a name)
  * __Have no child__

``` XML
<fields>
    <field tag="181">
        <subfield code="c" startPosition="0" endPosition="2">
            <value value="nda" name="A"/>
            <value value="ndb" name="B"/>
        </subfield>
        <subfield code="b" startPosition="0">
            <value value="f" name="Fake Appollo"/>
        </subfield>
        <subfield code="a">
            <value value="lovecolor" name="Love Colored Master Spark"/>
        </subfield>
    </field>
</fields>
```