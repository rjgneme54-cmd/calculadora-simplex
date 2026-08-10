export interface FractionValue {
  num: number;
  den: number;
  decimal: number;
}

export interface CellValue extends FractionValue {
  m_num: number;
  m_den: number;
}

export interface RatioTestRow {
  row: number;
  basic_var: string;
  rhs: CellValue;
  coeff: CellValue;
  ratio: FractionValue | null;
  eligible: boolean;
}

export interface TableauIteration {
  iteration: number;
  phase: number;
  basis: string[];
  var_names: string[];
  matrix: CellValue[][];
  rhs: CellValue[];
  z_row: CellValue[];
  z_value: CellValue;
  entering: string | null;
  leaving: string | null;
  pivot_row: number | null;
  pivot_col: number | null;
  pivot_element: CellValue | null;
  ratio_test: RatioTestRow[];
  explanation: string;
  is_optimal: boolean;
  is_degenerate_step: boolean;
}

export interface StandardFormData {
  var_names: string[];
  column_kinds: string[];
  objective_coeffs: FractionValue[];
  constraint_rows: FractionValue[][];
  rhs: FractionValue[];
  artificial_var_names: string[];
}

export type SolveStatus = "optimal" | "unbounded" | "infeasible";

export interface PlotPointData {
  x: number;
  y: number;
}

export interface LineSegmentData {
  label: string;
  point1: PlotPointData;
  point2: PlotPointData;
}

export interface GraphVertex {
  label: string;
  x: FractionValue;
  y: FractionValue;
  z: FractionValue;
}

export interface PlotBounds {
  xmin: number;
  xmax: number;
  ymin: number;
  ymax: number;
}

export interface GraphicalData {
  var_names: [string, string];
  lines: LineSegmentData[];
  feasible_vertices: GraphVertex[];
  optimal_vertices: GraphVertex[];
  objective_coeffs: [FractionValue, FractionValue];
  plot_bounds: PlotBounds;
  is_unbounded_region: boolean;
}

export interface ObjectiveCoeffRange {
  variable_name: string;
  current_value: FractionValue;
  lower: FractionValue | null;
  upper: FractionValue | null;
  applicable: boolean;
}

export interface RhsRangeItem {
  constraint_name: string;
  current_value: FractionValue;
  lower: FractionValue | null;
  upper: FractionValue | null;
  shadow_price: FractionValue;
}

export interface SensitivityData {
  objective_ranges: ObjectiveCoeffRange[];
  rhs_ranges: RhsRangeItem[];
}

export type DualVariableSign = "nonnegative" | "nonpositive" | "free";

export interface DualVariable {
  name: string;
  primal_constraint_name: string;
  sign: DualVariableSign;
  value: FractionValue;
}

export interface DualConstraint {
  primal_variable_name: string;
  coeffs: FractionValue[];
  op: "<=" | ">=" | "=";
  rhs: FractionValue;
}

export interface ComplementarySlacknessItem {
  description: string;
  holds: boolean;
}

export interface DualData {
  dual_sense: "max" | "min";
  dual_variables: DualVariable[];
  dual_constraints: DualConstraint[];
  dual_objective_coeffs: FractionValue[];
  primal_z: FractionValue;
  dual_z: FractionValue;
  strong_duality_holds: boolean;
  complementary_slackness: ComplementarySlacknessItem[];
}

export type BranchBoundOutcome = "branched" | "pruned_infeasible" | "pruned_bound" | "pruned_integer";

export interface BranchBoundNode {
  id: number;
  parent_id: number | null;
  depth: number;
  branch_description: string | null;
  status: string;
  solution: Record<string, FractionValue> | null;
  z: FractionValue | null;
  is_integer_feasible: boolean;
  outcome: BranchBoundOutcome;
  branched_variable: string | null;
}

export interface BranchAndBoundData {
  status: "optimal" | "infeasible";
  solution: Record<string, FractionValue> | null;
  z: FractionValue | null;
  nodes: BranchBoundNode[];
  message: string;
}

export interface SolveResponse {
  status: SolveStatus;
  method: "two_phase" | "big_m";
  message: string;
  standard_form: StandardFormData;
  iterations: TableauIteration[];
  solution: Record<string, FractionValue> | null;
  z: FractionValue | null;
  has_alternate_optima: boolean;
  is_degenerate: boolean;
  graphical: GraphicalData | null;
  sensitivity: SensitivityData | null;
  dual: DualData | null;
  branch_and_bound: BranchAndBoundData | null;
}

export interface SolveRequestPayload {
  sense: "max" | "min";
  objective: number[];
  variables: { name: string; sign: string; kind: string }[];
  constraints: { coeffs: number[]; op: string; rhs: number; name?: string }[];
  method: "two_phase" | "big_m";
}

export interface ExampleProblem {
  id: string;
  title: string;
  description: string;
  request: SolveRequestPayload;
}
