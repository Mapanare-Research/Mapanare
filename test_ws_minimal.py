from mapanare.cli import _compile_to_llvm_ir
from pathlib import Path

ws = Path('stdlib/net/websocket.mn').read_text(encoding='utf-8')
src = ws + '\n\nfn main() {\n    let conn: WsConnection = new_ws_connection(5, 0, false, false)\n    println("ok")\n}\n'

import mapanare.emit_llvm_mir as em
orig = em.LLVMMIREmitter._emit_call

def debug_emit_call(self, inst, builder, values, func):
    try:
        return orig(self, inst, builder, values, func)
    except TypeError as e:
        print(f'CALL FAILED in fn: {func.name}')
        print(f'  inst.fn_name={inst.fn_name}')
        print(f'  inst.args={inst.args}')
        for i, a in enumerate(inst.args):
            if a in values:
                print(f'  arg[{i}] {a} -> llvm type: {values[a].type}')
            else:
                print(f'  arg[{i}] {a} -> NOT IN VALUES')
        raise

em.LLVMMIREmitter._emit_call = debug_emit_call

try:
    _compile_to_llvm_ir(src, 'test.mn', use_mir=True)
    print('OK')
except TypeError as e:
    print(f'Error: {e}')
