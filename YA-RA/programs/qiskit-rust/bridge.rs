// The Rust side of the plane. The firmware declares one symbol in
// interface.txt; this file must export exactly that symbol, or the two halves
// do not meet and the Intent is contradicted.
#[no_mangle]
pub extern "C" fn yara_qpu_submit(circuit: *const u8, len: usize) -> i32 {
    if circuit.is_null() || len == 0 { return -1; }
    0
}
