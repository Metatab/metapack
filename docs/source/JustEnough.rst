Just Enough Metatab
===================

To fully understand this documentation, you'll want to have a basic
understanding of Metatab. The best information is in the `Specification
<https://github.com/Metatab/metatab-declarations/blob/master/specs/Metatab%20Spe
cification.md>`_, but you can get by with a short introduction.

Metatab is a tabular format for structured data, so you can put records that
have multiple properties and children into a spreadsheet. Each of the Metatab
records is a :code:`Term`. Terms have a short name and a fullt qualified name.
For instance, the term that holds title information is the :code:`Root.Title`
term, but can be shortened to :code:`Title`.

In a Metatab file, the first column always holds a term name, and the second
column holds the term value. The follwoing columns can hold properties, which
are also child terms.

Child Relationship are encoded by specifing a term that has the first part of
the fully qualified term be the same name as the parent term. For instance,
these rows:

+--------------+------------+
| Root.Table   | TableName  |
+--------------+------------+
| Table.Column | ColumnName |
+--------------+------------+
	
Will create a :code:`Root.Table` term, with a value of 'TableName' and a
:code:`Table.Column` child, with a column name of 'ColumnName'.

Rows can also have properties, values in the third column of the file or
later, which are converted to child properties. The term name for the
properties is specified in a header, which is part of the section the terms are
in. A Metatab document starts with a root section, but the section can be
explicitly set with a :code:`Section` term. Here is an example, from the
Schema section of a typical Metatab document:

+---------+------------+----------+
| Section | Schema     | DataType |
+---------+------------+----------+
| Table   | TableName  |          |
+---------+------------+----------+
| Column  | ColumnName | integer  |
+---------+------------+----------+

In the :code:`Section` row, the third column, "DataType" declares that in
this section, any value in the third column is a child of the row's term,
with a name of :code:`DataType`. Therefore, the third line of this example
results in a :code:`Table.Column` term with a value of "ColumnName" and the
:code:`Table.Column` term has a child term of type :code:`Column.DataType`
with a value of "integer"

For writing in text files, there is a "Text Lines" version of the format, which
consists of only the term and value portions of the format; all properties are
reptrsented as explicity children. This is the format you will see in this
documentation. For instance, the Schema section example would be expressed in
Text Lines as::

	Section: Schema
	Table: TableName
	Table.Column: ColumnName
	Column.DataType: Integer

