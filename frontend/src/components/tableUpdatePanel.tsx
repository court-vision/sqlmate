import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlusIcon, Trash2Icon } from "lucide-react";
import { TableUpdateAttribute, TableUpdateConstraint } from "@/types/http";

interface TableUpdatePanelProps {
  columns: { name: string; type: string }[];
  onSubmit: (
    updates: TableUpdateAttribute[],
    constraints: TableUpdateConstraint[]
  ) => void;
  isSubmitting: boolean;
}

type UpdateRow = {
  id: string;
  attribute: string;
  value: string;
};

type ConstraintRow = {
  id: string;
  attribute: string;
  operator: string;
  value: string;
};

export function TableUpdatePanel({
  columns,
  onSubmit,
  isSubmitting,
}: TableUpdatePanelProps) {
  // State for updates and constraints
  const [updates, setUpdates] = useState<UpdateRow[]>([
    { id: crypto.randomUUID(), attribute: "", value: "" },
  ]);

  const [constraints, setConstraints] = useState<ConstraintRow[]>([
    { id: crypto.randomUUID(), attribute: "", operator: "", value: "" },
  ]);

  // Add new update row
  const addUpdateRow = () => {
    setUpdates([
      ...updates,
      { id: crypto.randomUUID(), attribute: "", value: "" },
    ]);
  };

  // Add new constraint row
  const addConstraintRow = () => {
    setConstraints([
      ...constraints,
      { id: crypto.randomUUID(), attribute: "", operator: "", value: "" },
    ]);
  };

  // Remove update row
  const removeUpdateRow = (id: string) => {
    if (updates.length > 1) {
      setUpdates(updates.filter((update) => update.id !== id));
    }
  };

  // Remove constraint row
  const removeConstraintRow = (id: string) => {
    if (constraints.length > 1) {
      setConstraints(constraints.filter((constraint) => constraint.id !== id));
    }
  };

  // Handle update attribute change
  const handleUpdateAttributeChange = (id: string, attribute: string) => {
    setUpdates(
      updates.map((update) =>
        update.id === id ? { ...update, attribute } : update
      )
    );
  };

  // Handle update value change
  const handleUpdateValueChange = (id: string, value: string) => {
    setUpdates(
      updates.map((update) =>
        update.id === id ? { ...update, value } : update
      )
    );
  };

  // Handle constraint attribute change
  const handleConstraintAttributeChange = (id: string, attribute: string) => {
    setConstraints(
      constraints.map((constraint) =>
        constraint.id === id ? { ...constraint, attribute } : constraint
      )
    );
  };

  // Handle constraint operator change
  const handleConstraintOperatorChange = (id: string, operator: string) => {
    setConstraints(
      constraints.map((constraint) =>
        constraint.id === id ? { ...constraint, operator } : constraint
      )
    );
  };

  // Handle constraint value change
  const handleConstraintValueChange = (id: string, value: string) => {
    setConstraints(
      constraints.map((constraint) =>
        constraint.id === id ? { ...constraint, value } : constraint
      )
    );
  };

  // Handle form submission
  const handleSubmit = () => {
    // Filter out any rows with empty attributes
    const validUpdates: TableUpdateAttribute[] = updates
      .filter((update) => update.attribute && update.value !== "")
      .map((update) => ({
        attribute: update.attribute,
        value: update.value,
      }));

    const validConstraints: TableUpdateConstraint[] = constraints
      .filter((constraint) => constraint.attribute && constraint.operator)
      .map((constraint) => ({
        attribute: constraint.attribute,
        operator: constraint.operator,
        value: constraint.value,
      }));

    onSubmit(validUpdates, validConstraints);
  };

  const canSubmit =
    updates.some((u) => u.attribute && u.value !== "") &&
    constraints.some((c) => c.attribute && c.operator);

  return (
    <Card className="p-4 mb-6 glass hover-lift transition-all-smooth animate-slide-up">
      <h2 className="text-lg font-medium mb-3 gradient-text">Update Table</h2>

      {/* Updates Section */}
      <div className="mb-4">
        <h3 className="text-sm font-medium mb-2 gradient-text">
          Set New Values
        </h3>
        <div className="space-y-2 mb-2">
          {updates.map((update) => (
            <div key={update.id} className="flex items-center gap-2">
              <select
                className="glass-input rounded px-2 py-1 flex-1 transition-all-smooth focus:ring-primary"
                value={update.attribute}
                onChange={(e) =>
                  handleUpdateAttributeChange(update.id, e.target.value)
                }
              >
                <option value="">Select attribute</option>
                {columns.map((col, index) => (
                  <option key={`update-col-${index}`} value={col.name}>
                    {col.name}
                  </option>
                ))}
              </select>
              <span className="text-muted-foreground">=</span>
              <input
                type="text"
                className="glass-input rounded px-2 py-1 flex-1 transition-all-smooth focus:ring-primary"
                placeholder="New value"
                value={update.value}
                onChange={(e) =>
                  handleUpdateValueChange(update.id, e.target.value)
                }
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeUpdateRow(update.id)}
                disabled={updates.length <= 1}
                className="h-8 w-8 p-0 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all-smooth"
              >
                <Trash2Icon size={14} />
              </Button>
            </div>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          className="text-xs glass hover:bg-white/10 hover-glow transition-all-smooth"
          onClick={addUpdateRow}
        >
          <PlusIcon size={12} className="mr-1" /> Add Field
        </Button>
      </div>

      {/* Constraints Section */}
      <div className="mb-4">
        <h3 className="text-sm font-medium mb-2 gradient-text">
          Where (Constraints)
        </h3>
        <div className="space-y-2 mb-2">
          {constraints.map((constraint) => (
            <div key={constraint.id} className="flex items-center gap-2">
              <select
                className="glass-input rounded px-2 py-1 flex-1 transition-all-smooth focus:ring-primary"
                value={constraint.attribute}
                onChange={(e) =>
                  handleConstraintAttributeChange(constraint.id, e.target.value)
                }
              >
                <option value="">Select attribute</option>
                {columns.map((col, index) => (
                  <option key={`constraint-col-${index}`} value={col.name}>
                    {col.name}
                  </option>
                ))}
              </select>
              <select
                className="bg-transparent border border-input rounded px-2 py-1"
                value={constraint.operator}
                onChange={(e) =>
                  handleConstraintOperatorChange(constraint.id, e.target.value)
                }
              >
                <option value="">Operator</option>
                <option value="=">=</option>
                <option value="<">{"<"}</option>
                <option value=">">{">"}</option>
                <option value="<=">{"<="}</option>
                <option value=">=">{">="}</option>
                <option value="!=">{"!="}</option>
                <option value="PREFIX">{"PREFIX"}</option>
                <option value="SUFFIX">{"SUFFIX"}</option>
                <option value="SUBSTRING">{"SUBSTRING"}</option>
              </select>
              <input
                type="text"
                className="bg-transparent border border-input rounded px-2 py-1 flex-1"
                placeholder="Value"
                value={constraint.value}
                onChange={(e) =>
                  handleConstraintValueChange(constraint.id, e.target.value)
                }
                disabled={!constraint.operator}
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeConstraintRow(constraint.id)}
                disabled={constraints.length <= 1}
                className="h-8 w-8 p-0"
              >
                <Trash2Icon size={14} />
              </Button>
            </div>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          className="text-xs glass hover:bg-white/10 hover-glow transition-all-smooth"
          onClick={addConstraintRow}
        >
          <PlusIcon size={12} className="mr-1" /> Add Constraint
        </Button>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSubmit}
          disabled={!canSubmit || isSubmitting}
          className="w-full md:w-auto gradient-primary hover:shadow-lg hover:scale-105 transition-all-smooth"
        >
          {isSubmitting ? (
            <div className="flex items-center gap-2">
              <div className="spinner-gradient w-4 h-4"></div>
              Updating...
            </div>
          ) : (
            "Update Table"
          )}
        </Button>
      </div>
    </Card>
  );
}
