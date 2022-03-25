import logging

from netqasm import NETQASM_VERSION
from netqasm.backend.messages import deserialize_host_msg as deserialize_message
from netqasm.backend.network_stack import CREATE_FIELDS
from netqasm.backend.network_stack import OK_FIELDS_K as OK_FIELDS
from netqasm.lang import instr as instructions
from netqasm.lang.encoding import RegisterName
from netqasm.lang.operand import Address, ArrayEntry, ArraySlice, Immediate, Register
from netqasm.lang.parsing import deserialize as deserialize_subroutine
from netqasm.lang.parsing.text import parse_text_subroutine
from netqasm.lang.subroutine import Subroutine
from netqasm.logging.glob import set_log_level
from netqasm.qlink_compat import EPRType, TimeUnit
from netqasm.sdk.connection import DebugConnection
from netqasm.sdk.epr_socket import EPRSocket
from netqasm.sdk.qubit import Qubit

DebugConnection.node_ids = {
    "Alice": 0,
    "Bob": 1,
}


def test_simple():
    set_log_level(logging.DEBUG)
    with DebugConnection("Alice") as alice:
        q1 = Qubit(alice)
        q2 = Qubit(alice)
        q1.H()
        q2.X()
        q1.X()
        q2.H()

    # 4 messages: init, subroutine, stop app and stop backend
    assert len(alice.storage) == 4
    raw_subroutine = deserialize_message(raw=alice.storage[1]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    expected = Subroutine(
        netqasm_version=NETQASM_VERSION,
        app_id=0,
        instructions=[
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(0),
            ),
            instructions.core.QAllocInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.InitInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(1),
            ),
            instructions.core.QAllocInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.InitInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(0),
            ),
            instructions.vanilla.GateHInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(1),
            ),
            instructions.vanilla.GateXInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(0),
            ),
            instructions.vanilla.GateXInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(1),
            ),
            instructions.vanilla.GateHInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            # NOTE qubits are now freed when application ends
            # without explicit qfree for each
            # Command(instruction=Instruction.SET, operands=[
            #     Register(RegisterName.Q, 0),
            #     0,
            # ]),
            # Command(instruction=Instruction.QFREE, operands=[
            #     Register(RegisterName.Q, 0),
            # ]),
            # Command(instruction=Instruction.SET, operands=[
            #     Register(RegisterName.Q, 0),
            #     1,
            # ]),
            # Command(instruction=Instruction.QFREE, operands=[
            #     Register(RegisterName.Q, 0),
            # ]),
        ],
    )
    for instr, expected_instr in zip(subroutine.instructions, expected.instructions):
        print(repr(instr))
        print(repr(expected_instr))
        assert instr == expected_instr
    print(subroutine)
    print(expected)


def test_rotations():
    set_log_level(logging.DEBUG)
    with DebugConnection("Alice") as alice:
        q = Qubit(alice)
        q.rot_X(n=1, d=1)

    # 4 messages: init, subroutine, stop app and stop backend
    assert len(alice.storage) == 4
    raw_subroutine = deserialize_message(raw=alice.storage[1]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    expected = Subroutine(
        netqasm_version=NETQASM_VERSION,
        app_id=0,
        instructions=[
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(0),
            ),
            instructions.core.QAllocInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.InitInstruction(
                reg=Register(RegisterName.Q, 0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.Q, 0),
                imm=Immediate(0),
            ),
            instructions.vanilla.RotXInstruction(
                reg=Register(RegisterName.Q, 0),
                imm0=Immediate(1),
                imm1=Immediate(1),
            ),
        ],
    )
    for instr, expected_instr in zip(subroutine.instructions, expected.instructions):
        print(repr(instr))
        print(repr(expected_instr))
        assert instr == expected_instr
    print(subroutine)
    print(expected)


def test_epr():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_app_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        q1 = epr_socket.create()[0]
        q1.H()

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    raw_subroutine = deserialize_message(raw=alice.storage[2]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    print(subroutine)

    expected_text = """
# NETQASM 0.0
# APPID 0
set R5 10
array R5 @0
set R5 1
array R5 @1
set R5 0
set R6 0
store R5 @1[R6]
set R5 20
array R5 @2
set R5 0
set R6 0
store R5 @2[R6]
set R5 1
set R6 1
store R5 @2[R6]
set R5 1
set R6 0
set R7 1
set R8 2
set R9 0
create_epr R5 R6 R7 R8 R9
set R5 0
set R6 10
wait_all @0[R5:R6]
set R2 0
set R5 1
beq R2 R5 50
load R0 @1[R2]
set R3 9
set R4 0
beq R4 R2 36
set R5 10
add R3 R3 R5
set R5 1
add R4 R4 R5
jmp 30
load R1 @0[R3]
set R5 1
bne R1 R5 40
rot_z R0 16 4
set R5 2
bne R1 R5 43
rot_x R0 16 4
set R5 3
bne R1 R5 47
rot_x R0 16 4
rot_z R0 16 4
set R5 1
add R2 R2 R5
jmp 25
set Q0 0
h Q0
ret_arr @0
ret_arr @1
ret_arr @2
"""

    expected = parse_text_subroutine(expected_text)

    for i, instr in enumerate(subroutine.instructions):
        print(repr(instr))
        expected_instr = expected.instructions[i]
        print(repr(expected_instr))
        print()
        assert instr == expected_instr
    print(subroutine)
    print(expected)


def test_two_epr():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_app_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        qubits = epr_socket.create(number=2)
        qubits[0].H()
        qubits[1].H()

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    raw_subroutine = deserialize_message(raw=alice.storage[2]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    print(subroutine)

    expected_text = """
# NETQASM 0.0
# APPID 0
set R5 20
array R5 @0
set R5 2
array R5 @1
set R5 0
set R6 0
store R5 @1[R6]
set R5 1
set R6 1
store R5 @1[R6]
set R5 20
array R5 @2
set R5 0
set R6 0
store R5 @2[R6]
set R5 2
set R6 1
store R5 @2[R6]
set R5 1
set R6 0
set R7 1
set R8 2
set R9 0
create_epr R5 R6 R7 R8 R9
set R5 0
set R6 20
wait_all @0[R5:R6]
set R2 0
set R5 2
beq R2 R5 53
load R0 @1[R2]
set R3 9
set R4 0
beq R4 R2 39
set R5 10
add R3 R3 R5
set R5 1
add R4 R4 R5
jmp 33
load R1 @0[R3]
set R5 1
bne R1 R5 43
rot_z R0 16 4
set R5 2
bne R1 R5 46
rot_x R0 16 4
set R5 3
bne R1 R5 50
rot_x R0 16 4
rot_z R0 16 4
set R5 1
add R2 R2 R5
jmp 28
set Q0 0
h Q0
set Q0 1
h Q0
ret_arr @0
ret_arr @1
ret_arr @2
    """

    expected = parse_text_subroutine(expected_text)

    for i, instr in enumerate(subroutine.instructions):
        print(repr(instr))
        expected_instr = expected.instructions[i]
        print(repr(expected_instr))
        assert instr == expected_instr
    print(subroutine)
    print(expected)


def test_epr_m():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_app_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        outcomes = epr_socket.create_measure()
        m = outcomes[0].raw_measurement_outcome
        with m.if_eq(0):
            m.add(1)

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    raw_subroutine = deserialize_message(raw=alice.storage[2]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    print(subroutine)
    expected = Subroutine(
        netqasm_version=NETQASM_VERSION,
        app_id=0,
        instructions=[
            # Arg array
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(OK_FIELDS),
            ),
            instructions.core.ArrayInstruction(
                reg=Register(RegisterName.R, 1),
                address=Address(0),
            ),
            # ent info array
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(CREATE_FIELDS),
            ),
            instructions.core.ArrayInstruction(
                reg=Register(RegisterName.R, 1),
                address=Address(1),
            ),
            # tp arg
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(0),
            ),
            instructions.core.StoreInstruction(
                reg=Register(RegisterName.R, 1),
                entry=ArrayEntry(1, index=Register(RegisterName.R, 2)),
            ),
            # num pairs arg
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(1),
            ),
            instructions.core.StoreInstruction(
                reg=Register(RegisterName.R, 1),
                entry=ArrayEntry(1, index=Register(RegisterName.R, 2)),
            ),
            # create cmd
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 3),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 4),
                imm=Immediate(0),
            ),
            instructions.core.CreateEPRInstruction(
                reg0=Register(RegisterName.R, 1),
                reg1=Register(RegisterName.R, 2),
                reg2=Register(RegisterName.C, 0),
                reg3=Register(RegisterName.R, 3),
                reg4=Register(RegisterName.R, 4),
            ),
            # wait cmd
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(OK_FIELDS),
            ),
            instructions.core.WaitAllInstruction(
                slice=ArraySlice(
                    address=Address(0),
                    start=Register(RegisterName.R, 1),
                    stop=Register(RegisterName.R, 2),
                ),
            ),
            # if statement
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(2),
            ),
            instructions.core.LoadInstruction(
                reg=Register(RegisterName.R, 0),
                entry=ArrayEntry(
                    address=Address(0),
                    index=Register(RegisterName.R, 1),
                ),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(0),
            ),
            instructions.core.BneInstruction(
                reg0=Register(RegisterName.R, 0),
                reg1=Register(RegisterName.R, 1),
                imm=Immediate(28),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(2),
            ),
            instructions.core.LoadInstruction(
                reg=Register(RegisterName.R, 0),
                entry=ArrayEntry(
                    address=Address(0),
                    index=Register(RegisterName.R, 1),
                ),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(1),
            ),
            instructions.core.AddInstruction(
                reg0=Register(RegisterName.R, 0),
                reg1=Register(RegisterName.R, 0),
                reg2=Register(RegisterName.R, 1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(2),
            ),
            instructions.core.StoreInstruction(
                reg=Register(RegisterName.R, 0),
                entry=ArrayEntry(
                    address=Address(0),
                    index=Register(RegisterName.R, 1),
                ),
            ),
            # return cmds
            instructions.core.RetArrInstruction(
                address=Address(0),
            ),
            instructions.core.RetArrInstruction(
                address=Address(1),
            ),
        ],
    )
    for i, instr in enumerate(subroutine.instructions):
        print(repr(instr))
        expected_instr = expected.instructions[i]
        print(repr(expected_instr))
        print()
        assert instr == expected_instr
    print(subroutine)
    print(expected)


def test_epr_r_create():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_app_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        outcomes = epr_socket.create(tp=EPRType.R)
        m = outcomes[0].raw_measurement_outcome
        with m.if_eq(0):
            m.add(1)

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    raw_subroutine = deserialize_message(raw=alice.storage[2]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    expected = Subroutine(
        netqasm_version=NETQASM_VERSION,
        app_id=0,
        instructions=[
            # Arg array
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(OK_FIELDS),
            ),
            instructions.core.ArrayInstruction(
                reg=Register(RegisterName.R, 1),
                address=Address(0),
            ),
            # ent info array
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(CREATE_FIELDS),
            ),
            instructions.core.ArrayInstruction(
                reg=Register(RegisterName.R, 1),
                address=Address(1),
            ),
            # tp arg
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(2),  # EPRType.R
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(0),
            ),
            instructions.core.StoreInstruction(
                reg=Register(RegisterName.R, 1),
                entry=ArrayEntry(1, index=Register(RegisterName.R, 2)),
            ),
            # num pairs arg
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(1),
            ),
            instructions.core.StoreInstruction(
                reg=Register(RegisterName.R, 1),
                entry=ArrayEntry(1, index=Register(RegisterName.R, 2)),
            ),
            # create cmd
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 3),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 4),
                imm=Immediate(0),
            ),
            instructions.core.CreateEPRInstruction(
                reg0=Register(RegisterName.R, 1),
                reg1=Register(RegisterName.R, 2),
                reg2=Register(RegisterName.C, 0),
                reg3=Register(RegisterName.R, 3),
                reg4=Register(RegisterName.R, 4),
            ),
            # wait cmd
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(OK_FIELDS),
            ),
            instructions.core.WaitAllInstruction(
                slice=ArraySlice(
                    address=Address(0),
                    start=Register(RegisterName.R, 1),
                    stop=Register(RegisterName.R, 2),
                ),
            ),
            # if statement
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(2),
            ),
            instructions.core.LoadInstruction(
                reg=Register(RegisterName.R, 0),
                entry=ArrayEntry(
                    address=Address(0),
                    index=Register(RegisterName.R, 1),
                ),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(0),
            ),
            instructions.core.BneInstruction(
                reg0=Register(RegisterName.R, 0),
                reg1=Register(RegisterName.R, 1),
                imm=Immediate(28),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(2),
            ),
            instructions.core.LoadInstruction(
                reg=Register(RegisterName.R, 0),
                entry=ArrayEntry(
                    address=Address(0),
                    index=Register(RegisterName.R, 1),
                ),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(1),
            ),
            instructions.core.AddInstruction(
                reg0=Register(RegisterName.R, 0),
                reg1=Register(RegisterName.R, 0),
                reg2=Register(RegisterName.R, 1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(2),
            ),
            instructions.core.StoreInstruction(
                reg=Register(RegisterName.R, 0),
                entry=ArrayEntry(
                    address=Address(0),
                    index=Register(RegisterName.R, 1),
                ),
            ),
            # return cmds
            instructions.core.RetArrInstruction(
                address=Address(0),
            ),
            instructions.core.RetArrInstruction(
                address=Address(1),
            ),
        ],
    )
    for i, instr in enumerate(subroutine.instructions):
        print(repr(instr))
        expected_instr = expected.instructions[i]
        print(repr(expected_instr))
        print()
        assert instr == expected_instr
    print(f"subroutine: {subroutine}")
    print(f"expected: {expected}")


def test_epr_r_receive():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_app_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        _ = epr_socket.recv(tp=EPRType.R)[0]

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    raw_subroutine = deserialize_message(raw=alice.storage[2]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    print(subroutine)
    expected = Subroutine(
        netqasm_version=NETQASM_VERSION,
        app_id=0,
        instructions=[
            # Arg array
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 0),
                imm=Immediate(OK_FIELDS),
            ),
            instructions.core.ArrayInstruction(
                reg=Register(RegisterName.R, 0),
                address=Address(0),
            ),
            # Qubit address array
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 0),
                imm=Immediate(1),
            ),
            instructions.core.ArrayInstruction(
                reg=Register(RegisterName.R, 0),
                address=Address(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 0),
                imm=Immediate(0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(0),
            ),
            instructions.core.StoreInstruction(
                reg=Register(RegisterName.R, 0),
                entry=ArrayEntry(1, index=Register(RegisterName.R, 1)),
            ),
            # create cmd
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 0),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 2),
                imm=Immediate(1),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 3),
                imm=Immediate(0),
            ),
            instructions.core.RecvEPRInstruction(
                reg0=Register(RegisterName.R, 0),
                reg1=Register(RegisterName.R, 1),
                reg2=Register(RegisterName.R, 2),
                reg3=Register(RegisterName.R, 3),
            ),
            # wait cmd
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 0),
                imm=Immediate(0),
            ),
            instructions.core.SetInstruction(
                reg=Register(RegisterName.R, 1),
                imm=Immediate(OK_FIELDS),
            ),
            instructions.core.WaitAllInstruction(
                slice=ArraySlice(
                    address=Address(0),
                    start=Register(RegisterName.R, 0),
                    stop=Register(RegisterName.R, 1),
                ),
            ),
            instructions.core.RetArrInstruction(
                address=Address(0),
            ),
            instructions.core.RetArrInstruction(
                address=Address(1),
            ),
        ],
    )
    for i, instr in enumerate(subroutine.instructions):
        print(f"actual command: {repr(instr)}")
        expected_instr = expected.instructions[i]
        print(f"expected command: {repr(expected_instr)}")
        print()
        assert instr == expected_instr
    print(f"actual: {subroutine}")
    print(f"expected: {expected}")


def test_epr_max_time():

    set_log_level(logging.DEBUG)

    epr_socket = EPRSocket(remote_app_name="Bob")
    with DebugConnection("Alice", epr_sockets=[epr_socket]) as alice:
        q1 = epr_socket.create(time_unit=TimeUnit.MILLI_SECONDS, max_time=25)[0]
        q1.H()

    # 5 messages: init, open_epr_socket, subroutine, stop app and stop backend
    assert len(alice.storage) == 5
    raw_subroutine = deserialize_message(raw=alice.storage[2]).subroutine
    subroutine = deserialize_subroutine(raw_subroutine)
    print(subroutine)

    expected_text = """
# NETQASM 0.0
# APPID 0
set R5 10
array R5 @0
set R5 1
array R5 @1
set R5 0
set R6 0
store R5 @1[R6]
set R5 20
array R5 @2
set R5 0
set R6 0
store R5 @2[R6]
set R5 1
set R6 1
store R5 @2[R6]
set R5 1
set R6 5
store R5 @2[R6]
set R5 25
set R6 6
store R5 @2[R6]
set R5 1
set R6 0
set R7 1
set R8 2
set R9 0
create_epr R5 R6 R7 R8 R9
set R5 0
set R6 10
wait_all @0[R5:R6]
set R2 0
set R5 1
beq R2 R5 56
load R0 @1[R2]
set R3 9
set R4 0
beq R4 R2 42
set R5 10
add R3 R3 R5
set R5 1
add R4 R4 R5
jmp 36
load R1 @0[R3]
set R5 1
bne R1 R5 46
rot_z R0 16 4
set R5 2
bne R1 R5 49
rot_x R0 16 4
set R5 3
bne R1 R5 53
rot_x R0 16 4
rot_z R0 16 4
set R5 1
add R2 R2 R5
jmp 31
set Q0 0
h Q0
ret_arr @0
ret_arr @1
ret_arr @2
    """

    expected = parse_text_subroutine(expected_text)

    for i, instr in enumerate(subroutine.instructions):
        print(repr(instr))
        expected_instr = expected.instructions[i]
        print(repr(expected_instr))
        assert instr == expected_instr
    print(subroutine)
    print(expected)
    assert subroutine == expected


if __name__ == "__main__":
    test_simple()
    test_rotations()
    test_epr()
    test_two_epr()
    test_epr_m()
    test_epr_r_create()
    test_epr_r_receive()
    test_epr_max_time()
