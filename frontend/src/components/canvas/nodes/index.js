import StartNode from './StartNode';
import MessageNode from './MessageNode';
import QuestionNode from './QuestionNode';
import ConditionNode from './ConditionNode';
import VariableNode from './VariableNode';
import ResponseNode from './ResponseNode';
import EndNode from './EndNode';

/**
 * NODE_TYPES — mapa de tipo → componente visual.
 * Lo usa <ReactFlow nodeTypes={NODE_TYPES}>.
 *
 * Las claves coinciden exactamente con los valores de `node.type`
 * del builder (start, message, question, condition, variable, response, end).
 */
export const NODE_TYPES = {
  start: StartNode,
  message: MessageNode,
  question: QuestionNode,
  condition: ConditionNode,
  variable: VariableNode,
  response: ResponseNode,
  end: EndNode,
};

export {
  StartNode,
  MessageNode,
  QuestionNode,
  ConditionNode,
  VariableNode,
  ResponseNode,
  EndNode,
};
