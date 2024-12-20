use std::alloc::{alloc, dealloc, Layout};
use argon2::{Algorithm};

pub mod util;

#[no_mangle]
pub fn add(left: usize, right: usize) -> usize {
    left + right
}


// #[no_mangle]
// pub fn _argon2id(password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
//     let hash = util::argon2(Algorithm::Argon2id, password, salt, m, t, p, length);
//     hash
// }

#[no_mangle]
pub fn _argon2id(
    password_ptr: *const u8, password_len: usize,
    salt_ptr: *const u8, salt_len: usize,
    m: u32, t: u32, p: u32, length: u32
) -> u64 {
    let password = unsafe { std::slice::from_raw_parts(password_ptr, password_len) };
    let salt = unsafe { std::slice::from_raw_parts(salt_ptr, salt_len) };
    let hash = util::argon2(Algorithm::Argon2id, password, salt, m, t, p, length);
    let ptr = allocate(hash.len()) as *mut u8;
    let dst = unsafe { std::slice::from_raw_parts_mut(ptr, hash.len()) };
    dst.copy_from_slice(hash.as_slice());
    (ptr as u64) << 32 | hash.len() as u64
}


#[no_mangle]
pub fn allocate(size: usize) -> *mut u8 {
    let layout = Layout::from_size_align(size, 1).unwrap();
    let ptr = unsafe { alloc(layout) };
    if ptr.is_null() {
        panic!("Could not allocate memory");
    }
    ptr
}

#[no_mangle]
pub fn deallocate(ptr: *mut u8, size: usize) {
    let layout = Layout::from_size_align(size, 1).unwrap();
    unsafe {
        dealloc(ptr, layout);
    }
}

