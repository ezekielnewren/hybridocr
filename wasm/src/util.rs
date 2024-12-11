use argon2::{Algorithm, Argon2, Params, Version};
use nalgebra::{DMatrix, DVector};
use serde::{Deserialize, Serialize};


pub fn argon2(alg: Algorithm, password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
    let inst = Argon2::new(alg, Version::V0x13, Params::new(m, t, p, Some(length as usize)).unwrap());
    let mut buff = vec![0u8; length as usize];
    inst.hash_password_into(password, salt, &mut buff).expect("hashing failed");
    buff
}


#[derive(Serialize, Deserialize)]
pub struct Point {
    pub x: f32,
    pub y: f32,
}


pub fn midpoint(a: &Point, b: &Point) -> Point {
    Point{x: (a.x+b.x)/2.0, y: (a.y+b.y)/2.0}
}


pub fn distance(a: &Point, b: &Point) -> f32 {
    ((a.x-b.x).powi(2) + (a.y-b.y).powi(2)).sqrt()
}


pub fn transpose(src: &[u8], width: usize, height: usize, dst: &mut [u8]) -> Result<(), String> {
    if src.len() != dst.len() {
        return Err(String::from("src and dst length must be the same"));
    }
    if width*height != src.len() {
        return Err(String::from("the length of src must equal width*height"));
    }
    if width == 1 || height == 1 {
        dst.copy_from_slice(&src);
        return Ok(());
    }

    for col in 0..width {
        for row in 0..height {
            dst[col*height+row] = src[row*width+col];
        }
    }

    Ok(())
}


#[derive(Serialize, Deserialize)]
pub struct PixelBuffer {
    pub width: u32,
    pub height: u32,
    pub channels: u8,
    pub interleaved: bool,
    pub data: Vec<u8>,
}


impl PixelBuffer {

    pub fn new(width: u32, height: u32, channels: u8, interleaved: bool, src: &[u8]) -> Result<Self, String> {
        if width*height*channels as u32 != src.len() as u32 {
            return Err(String::from("width*height*channels must equal src.len()"));
        }

        Ok(Self {
            width,
            height,
            channels,
            interleaved,
            data: src.to_vec(),
        })
    }

    pub fn blank(width: u32, height: u32, channels: u8, interleaved: bool) -> Self {
        Self {
            width,
            height,
            channels,
            interleaved,
            data: vec![0u8; (width*height*channels as u32) as usize],
        }
    }

    pub fn toggle_interleaved(&mut self) {
        let mut w = self.channels as usize;
        let mut h = (self.width*self.height) as usize;
        if !self.interleaved {
            (w, h) = (h, w);
        }

        let src = self.data.clone();
        transpose(src.as_slice(), w, h, self.data.as_mut_slice()).unwrap();
        self.interleaved = !self.interleaved;
    }

    pub fn in_bounds(&self, x: f32, y: f32, c: u8) -> bool {
        let (w, h) = (self.width as f32, self.height as f32);
        0.0 <= x && x < w && 0.0 <= y && y < h && c < self.channels
    }

    pub fn get(&self, mut _x: f32, mut _y: f32, c: u8, closest: bool) -> u8 {
        if !self.in_bounds(_x, _y, c) {
            if closest {
                if _x < 0.0 {
                    _x = 0.0;
                } else if _x >= self.width as f32 {
                    _x = self.width as f32-1.0;
                }
                if _y < 0.0 {
                    _y = 0.0;
                } else if _y >= self.height as f32 {
                    _y = self.height as f32-1.0;
                }
            } else {
                return 0u8;
            }
        }
        let (w, h) = (self.width as usize, self.height as usize);
        let (x, y) = (_x as usize, _y as usize);
        if self.interleaved {
            let pixel_size = self.channels as usize;
            self.data[y*pixel_size*w + x*pixel_size + c as usize]
        } else {
            let channel_size = w*h;
            self.data[c as usize*channel_size + y*w + x]
        }
    }

    pub fn at_mut(&mut self, x: usize, y: usize, c: u8) -> &mut u8 {
        if !self.in_bounds(x as f32, y as f32, c) {
            panic!("Index out of bounds: x={}, y={}, c={}", x, y, c);
        }
        let (w, h) = (self.width as usize, self.height as usize);
        if self.interleaved {
            let pixel_size = self.channels as usize;
            &mut self.data[y*pixel_size*w + x*pixel_size + c as usize]
        } else {
            let channel_size = w*h;
            &mut self.data[c as usize*channel_size + y*w + x]
        }
    }
}


#[derive(Serialize, Deserialize)]
pub struct Quadrilateral {
    pub tl: Point,
    pub tr: Point,
    pub br: Point,
    pub bl: Point,
}


impl Quadrilateral {
    pub fn as_tuple_f32(&self) -> (f32, f32, f32, f32, f32, f32, f32, f32) {
        (
            self.tl.x,
            self.tl.y,
            self.tr.x,
            self.tr.y,
            self.br.x,
            self.br.y,
            self.bl.x,
            self.bl.y
        )
    }

    pub fn output_dimension(&self) -> (f32, f32) {
        let left_mid = midpoint(&self.tl, &self.bl);
        let right_mid = midpoint(&self.tr, &self.br);
        let width = distance(&left_mid, &right_mid);

        let top_mid = midpoint(&self.tl, &self.tr);
        let bot_mid = midpoint(&self.bl, &self.br);
        let height = distance(&top_mid, &bot_mid);

        (width.floor(), height.floor())
    }

    pub fn dst_quad(&self) -> Self {
        let (width, height) = self.output_dimension();

        Self {
            tl: Point{x: 0.0, y: 0.0},
            tr: Point{x: width, y: 0.0},
            br: Point{x: width, y: height},
            bl: Point{x: 0.0, y: height}
        }
    }
}


pub fn get_y_not_and_x_not(src: &Point, dst: &Point, out: &mut Vec<f32>) {
    out.push(0.0);
    out.push(0.0);
    out.push(0.0);
    out.push(-src.x);
    out.push(-src.y);
    out.push(-1.0);
    out.push(dst.y*src.x);
    out.push(dst.y*src.y);

    out.push(src.x);
    out.push(src.y);
    out.push(1.0);
    out.push(0.0);
    out.push(0.0);
    out.push(0.0);
    out.push(-dst.x*src.x);
    out.push(-dst.x*src.y);
}


pub fn get_homography_matrix(src: &Quadrilateral, dst: &Quadrilateral) -> [f32; 9] {
    let mut _a = Vec::<f32>::new();
    get_y_not_and_x_not(&src.tl, &dst.tl, &mut _a);
    get_y_not_and_x_not(&src.tr, &dst.tr, &mut _a);
    get_y_not_and_x_not(&src.br, &dst.br, &mut _a);
    get_y_not_and_x_not(&src.bl, &dst.bl, &mut _a);
    let a = DMatrix::from_row_slice(8, 8, &_a);

    let _b = [-dst.tl.y, dst.tl.x, -dst.tr.y, dst.tr.x, -dst.br.y, dst.br.x, -dst.bl.y, dst.bl.x];
    let b = DVector::from_column_slice(&_b);

    let solution = a.lu().solve(&b).unwrap();
    let mut h = [1.0; 9];
    h[..8].copy_from_slice(solution.as_slice());
    h
}


pub fn weight_cubic(span: &[u8], w: f32) -> u8 {
    let p0 = span[0] as f32;
    let p1 = span[1] as f32;
    let p2 = span[2] as f32;
    let p3 = span[3] as f32;

    let value = p1 + 0.5 * w * (p2 - p0
        + w * (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3
        + w * (3.0 * (p1 - p2) + p3 - p0)));

    value.clamp(0.0, 255.0) as u8
}


pub fn blend_cubic(src: &PixelBuffer, x: f32, y: f32, c: u8) -> u8 {
    let mut t = [0u8; 4];
    for rowi in 0..4 {
        let y_off = y+rowi as f32-2.0;
        let row = [
            src.get(x-2.0, y_off, c, true),
            src.get(x-1.0, y_off, c, true),
            src.get(x+0.0, y_off, c, true),
            src.get(x+1.0, y_off, c, true),
        ];

        let value = weight_cubic(&row, x-x.floor());
        t[rowi as usize] = value;
    }

    weight_cubic(&t, y-y.floor())
}


pub fn _pt(src: PixelBuffer, quad: Quadrilateral) -> Result<PixelBuffer, String> {
    let out_dim = quad.output_dimension();
    let c = src.channels;
    let mut dst = PixelBuffer::blank(out_dim.0 as u32, out_dim.1 as u32, c, src.interleaved);

    let h = get_homography_matrix(&quad.dst_quad(), &quad);

    for c in 0..c {
        for dst_y in 0..dst.height as usize {
            let y = dst_y as f32;
            for dst_x in 0..dst.width as usize {
                let x = dst_x as f32;

                let denom = h[6]*x + h[7]*y + h[8];
                if denom == 0.0 {
                    continue;
                }

                let src_x = (h[0]*x + h[1]*y + h[2])/denom;
                let src_y = (h[3]*x + h[4]*y + h[5])/denom;

                if !src.in_bounds(src_x, src_y, c) {
                    continue;
                }
                *dst.at_mut(dst_x, dst_y, c) = blend_cubic(&src, src_x, src_y, c)
            }
        }
    }

    Ok(dst)
}




