use std::alloc::{alloc, dealloc, Layout};
use argon2::{Algorithm};

use wee_alloc::WeeAlloc;
#[global_allocator]
static ALLOC: WeeAlloc = WeeAlloc::INIT;

pub mod util;

#[no_mangle]
pub fn add(left: usize, right: usize) -> usize {
    left + right
}

#[no_mangle]
pub fn _argon2id(
    _password: *mut u8,
    _salt: *mut u8,
    m: u32, t: u32, p: u32, length: u32
) -> *mut u8 {
    let mut password = util::Data::from_pointer(_password);
    let mut salt = util::Data::from_pointer(_salt);
    let hash = util::argon2(Algorithm::Argon2id, password.as_slice_mut(), salt.as_slice_mut(), m, t, p, length);
    let ptr = util::Data::new(hash.len());
    let dst = ptr.as_slice_mut();
    dst.copy_from_slice(hash.as_slice());
    salt.free();
    password.free();
    ptr.ptr
}


#[no_mangle]
pub fn allocate(size: usize) -> *mut u8 {
    let ptr_size = size_of::<usize>();
    let layout = Layout::from_size_align(ptr_size+size, 1).unwrap();
    let ptr = unsafe { alloc(layout) };
    for i in 0..ptr_size {
        unsafe {
            *ptr.add(i) = (size>>(i*8)) as u8;
        }
    }
    if ptr.is_null() {
        panic!("Could not allocate memory");
    }
    ptr
}

#[no_mangle]
pub fn deallocate(ptr: *mut u8, size: usize) {
    let ptr_size = size_of::<usize>();
    let layout = Layout::from_size_align(ptr_size+size, 1).unwrap();
    let mut _size = 0usize;
    for i in 0..ptr_size {
        let b = unsafe { *ptr.add(i) as usize };
        _size |= b<<(i*8);
    }
    assert_eq!(size, _size, "mismatched allocation size");
    unsafe {
        dealloc(ptr, layout);
    }
}

