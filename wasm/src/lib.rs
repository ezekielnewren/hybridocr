use std::alloc::{alloc, dealloc, Layout};
use argon2::{Algorithm};

use wee_alloc::WeeAlloc;
use crate::util::{Data, PixelBuffer, Point, Quadrilateral, _pt};

// #[global_allocator]
// static ALLOC: WeeAlloc = WeeAlloc::INIT;

pub mod util;


const POINTER_LENGTH: usize = size_of::<usize>();


#[no_mangle]
pub fn sandbox(_points: *mut u8) -> f32 {
    let points = Data::from_pointer(_points);
    let t = points.as_slice();
    let a = unsafe {
        let ptr = t.as_ptr() as *mut f32;
        std::slice::from_raw_parts(ptr, t.len())
    };
    a[0]
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
    ptr.as_slice_mut().copy_from_slice(hash.as_slice());
    salt.free();
    password.free();
    ptr.ptr
}


#[no_mangle]
pub fn perspective_transform(__pb: *mut u8, __quad: *mut u8, __answer: *mut u8) -> bool {
    let _pb = Data::from_pointer(__pb);
    let pb = PixelBuffer::from_data(&_pb).unwrap();

    let _quad = Data::from_pointer(__quad);
    let quad = Quadrilateral::from_data(&_quad);
    _quad.free();
    let mut answer = Data::from_pointer(__answer);

    let result = _pt(pb, quad);
    match result {
        Ok(v) => {
            let out: Data = v.into_data();
            unsafe {
                *(answer.ptr as *mut usize) = out.ptr as usize;
            }
            _pb.free();
            true
        }
        Err(e) => {
            let t = e.as_bytes();
            let out = Data::new(t.len());
            out.as_slice_mut().copy_from_slice(t);
            unsafe {
                *(answer.ptr as *mut usize) = out.ptr as usize;
            }
            _pb.free();
            false
        }
    }


}


#[no_mangle]
pub fn pointer_length() -> u32 {
    POINTER_LENGTH as u32
}


#[no_mangle]
pub fn memory_length(ptr: *mut u8) -> usize {
    let _ptr = unsafe { ptr.sub(POINTER_LENGTH) };
    let mut size = 0usize;
    for i in 0..POINTER_LENGTH {
        let b = unsafe { *_ptr.add(i) as usize };
        size |= b<<(i*8);
    }
    size
}


#[no_mangle]
pub fn w_malloc(size: usize) -> *mut u8 {
    let layout = Layout::from_size_align(POINTER_LENGTH+size, 1).unwrap();
    let _ptr = unsafe { alloc(layout) };
    for i in 0..POINTER_LENGTH {
        unsafe {
            *_ptr.add(i) = (size>>(i*8)) as u8;
        }
    }
    if _ptr.is_null() {
        panic!("Could not allocate memory");
    }
    let ptr = unsafe { _ptr.add(POINTER_LENGTH) };
    ptr
}

#[no_mangle]
pub fn w_free(ptr: *mut u8) {
    let len = memory_length(ptr);
    let _ptr = unsafe { ptr.sub(POINTER_LENGTH) };
    let layout = Layout::from_size_align(POINTER_LENGTH+len, 1).unwrap();
    unsafe {
        dealloc(_ptr, layout);
    }
}

