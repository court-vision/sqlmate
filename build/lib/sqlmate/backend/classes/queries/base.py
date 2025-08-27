from sqlmate.backend.classes.metadata import metadata
from typing import List
from sqlmate.backend.classes.http import QueryParams, UpdateQueryParams


# Class that will be used to initialize a TableQuery object
# which we will use to generate the query
class BaseQuery:
    def __init__(self, input: QueryParams | UpdateQueryParams, username: str = "") -> None:
        self.table_name: str = self.format_table_name(username, input.get("table", ""))
        if not input.get("attributes") and not input.get("updates"):
            raise ValueError(f"No attribues or updates selected for {self.table_name} table")
        self.attributes: List[Attribute] = [Attribute(details, self.table_name) for details in input.get("attributes", [])]
        self.constraints: List[Constraint] = [Constraint(details, self.table_name) for details in input.get("constraints", [])]
        self.group_by: List[str] = [f"{self.table_name}.{attribute}" for attribute in input.get("group_by", [])]
        self.aggregations: List[Aggregation] = [Aggregation(details, self.table_name) for details in input.get("aggregations", [])]
        self.order_by: List[Ordering] = [Ordering(details, self.table_name) for details in input.get("order_by", [])]

        self.alias_map: dict = {}

        self.str_attributes = "".join([str(attribute) for attribute in self.attributes])
        self.str_constraints = "".join([str(constraint) for constraint in self.constraints])
        self.str_aggregations = "".join([str(aggregation) for aggregation in self.aggregations])
        self.str_order_by = "".join([str(ordering) for ordering in self.order_by])

    def format_table_name(self, username: str, table_name: str) -> str:
        if username:
            return f'u_{username}_{table_name}'
        return table_name

    def get_SELECT_clause(self, num_tables: int) -> str:
        clause = ""

        for attr in self.attributes:
            if agg_type := self.check_aggregation(attr.attribute):
                clause += f"{agg_type}({attr.attribute})"
                alias = attr.alias if attr.alias else "_".join([agg_type] + attr.attribute.split("."))
            else:
                clause += f"{attr.attribute}"
                alias = attr.alias if attr.alias else ("_".join(attr.attribute.split(".")) if num_tables > 1 else attr.attribute.split(".")[-1])
            self.alias_map[attr.attribute] = alias # For use in the ORDER BY clause
            clause += f" AS {alias},"
        clause = clause[:-1]

        return clause

    def get_FROM_clause(self) -> str:
        clause = self.table_name
        
        return clause

    def get_JOIN_clause(self, lhs: str) -> str:
        clause = f"{self.table_name} ON {metadata.get_edge(lhs, self.table_name)}"

        return clause
    
    def get_WHERE_clause(self) -> str:
        clause = ""
        for constraint in self.constraints:
            clause += f"{constraint.attribute} {constraint.operator} {constraint.value} AND "

        return clause
    
    def get_GROUP_BY_clause(self) -> str:
        clause = ','.join(self.group_by)

        return clause
    
    def get_ORDER_BY_clause(self) -> str:
        clause = ""

        for ordering in self.order_by:
            name_or_alias = self.alias_map.get(ordering.attribute, ordering.attribute)
            clause += f"{name_or_alias} {ordering.sort},"

        return clause

    # Returns the aggregation type of the column
    def check_aggregation(self, attr_name: str) -> str:
        for agg in self.aggregations:
            if agg.attribute == attr_name:
                return agg.type
        return ""

    def __str__(self) -> str:
        return f"""
        (
            'table': {self.table_name}
            'attributes': {self.str_attributes}
            'constraints': {self.str_constraints}
            'group_by': {", ".join(self.group_by)}
            'aggregations': {self.str_aggregations}
        )
        """

class Attribute:
    def __init__(self, input: dict, table_name: str) -> None:
        self.attribute: str = f"{table_name}.{input.get('attribute', '')}"
        self.alias: str = input.get("alias", "")

    def __str__(self) -> str:
        return f"""
            (
                'attribute': {self.attribute}
                'alias': {self.alias}
            )
        """


class Constraint:
    def __init__(self, input: dict, table_name: str) -> None:
        self.attribute: str = f'{table_name}.{input.get("attribute", "")}'
        self.operator: str = input.get("operator", "")
        self.value: str = self.process_value(input.get("value", ""))

    # Handles if we are comparing strings
    def process_value(self, value: str) -> str:
        table_name, attribute_name = self.attribute.split(".")
        db_type = metadata.get_type(table_name, attribute_name)
        if db_type in ["STR", "DATE"]:
            new_value = ""
            if self.operator in ["=", "!="]:
                new_value = f"'{value}'"
            else:
                if self.operator == "SUBSTRING":
                    new_value = f"'%{value}%'"
                elif self.operator == "PREFIX":
                    new_value = f"'{value}%'"
                elif self.operator == "SUFFIX":
                    new_value = f"'%{value}'" 
                self.operator = "LIKE"
        else:
            if value.isnumeric():
                new_value = value
            else:
                raise ValueError(f"Invalid value for constraint on {self.attribute}: {value}")

        return new_value

    def __str__(self) -> str:
        return f"""
            (
                'attribute': {self.attribute},
                'operator': {self.operator},
                'value': {self.value}
            )
        """


class Aggregation:
    def __init__(self, input: dict, table_name: str) -> None:
        self.attribute: str = (
            f'{table_name}.{input.get("attribute", "")}'
        )
        self.type: str = input.get("type", "")

    def __str__(self):
        return f"""
            (
                'attribute': {self.attribute}
                'type': {self.type}
            )
        """

class Ordering:
    def __init__(self, input: dict, table_name: str) -> None:
        self.attribute: str = f'{table_name}.{input.get("attribute", "")}'
        self.sort: str = input.get("sort", "")

    def __str__(self):
        return f"""
            (
                'attribute': {self.attribute}
                'sort': {self.sort}
            )
        """