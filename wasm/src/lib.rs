use std::alloc::{alloc, dealloc, Layout};
use argon2::{Algorithm};

use wee_alloc::WeeAlloc;
use crate::util::{Data, PixelBuffer, Point, Quadrilateral, _pt};

#[global_allocator]
static ALLOC: WeeAlloc = WeeAlloc::INIT;

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
pub fn perspective_transform(width: u32, height: u32, channels: u32, interleaved: bool, _data: *mut u8, _points: *mut u8, _answer: *mut u8) -> bool {
    let mut data = Data::from_pointer(_data);
    let mut points = Data::from_pointer(_points);
    let mut answer = Data::from_pointer(_answer);


    let pb = PixelBuffer::new(width as usize, height as usize, channels as usize, interleaved, data.as_slice().to_vec()).unwrap();
    let p = unsafe {
        std::slice::from_raw_parts(points.ptr as *const f32, points.len/4)
    };
    let quad = Quadrilateral::from_slice(p);
    let dst_quad = quad.output_dimension();
    let out = format!("{:?}\n{:?}", p, quad);
    if true {
        let t = out.as_bytes();
        let ans = Data::new(t.len());
        ans.as_slice_mut().copy_from_slice(t);
        unsafe {
            *(answer.ptr as *mut usize) = ans.ptr as usize;
        }
        return false;
    }


    let result = _pt(pb, quad);
    match result {
        Ok(v) => {
            let out = Data::new(10+v.data.len());
            let m = out.as_slice_mut();
            m[0..4].copy_from_slice(&(v.width as u32).to_le_bytes());
            m[4..8].copy_from_slice(&(v.height as u32).to_le_bytes());
            m[8] = v.channels as u8;
            m[9] = if v.interleaved { 1 } else { 0 };
            m[10..].copy_from_slice(v.data.as_slice());
            data.free();
            points.free();
            unsafe {
                *(answer.ptr as *mut usize) = out.ptr as usize;
            }
            true
        }
        Err(e) => {
            let t = e.as_bytes();
            let out = Data::new(t.len());
            out.as_slice_mut().copy_from_slice(t);
            unsafe {
                *(answer.ptr as *mut usize) = out.ptr as usize;
            }
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

