use argon2::{Algorithm, Argon2, Params, Version};
use nalgebra::{DMatrix, DVector};


pub fn argon2(alg: Algorithm, password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
    let inst = Argon2::new(alg, Version::V0x13, Params::new(m, t, p, Some(length as usize)).unwrap());
    let mut buff = vec![0u8; length as usize];
    inst.hash_password_into(password, salt, &mut buff).expect("hashing failed");
    buff
}


pub struct Point {
    pub x: f32,
    pub y: f32,
}


pub struct HMatrix {
    h00: f32,
    h01: f32,
    h02: f32,
    h10: f32,
    h11: f32,
    h12: f32,
    h20: f32,
    h21: f32,
    h22: f32,
}

impl HMatrix {
    pub fn map(&self, x: f32, y: f32) -> Point {
        let denom = self.h20*x + self.h21*y + self.h22;
        Point{
            x: (self.h00*x + self.h01*y + self.h02)/denom,
            y: (self.h10*x + self.h11*y + self.h12)/denom,
        }
    }

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


pub struct PixelBuffer {
    pub width: usize,
    pub height: usize,
    pub channels: usize,
    pub interleaved: bool,
    pub data: Vec<u8>,
}


impl PixelBuffer {

    pub fn new(width: usize, height: usize, channels: usize, interleaved: bool, src: Vec<u8>) -> Result<Self, String> {
        if width*height*channels != src.len() {
            return Err(String::from("width*height*channels must equal src.len()"));
        }

        Ok(Self {
            width,
            height,
            channels,
            interleaved,
            data: src,
        })
    }

    pub fn blank(width: usize, height: usize, channels: usize, interleaved: bool) -> Self {
        Self {
            width,
            height,
            channels,
            interleaved,
            data: vec![0u8; width*height*channels],
            // data: Vec::<u8>::with_capacity(width*height*channels),
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
}


pub struct Quadrilateral {
    pub tl: Point,
    pub tr: Point,
    pub br: Point,
    pub bl: Point,
}


impl Quadrilateral {
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
            tl: Point{x: 0.0,   y: 0.0},
            tr: Point{x: width, y: 0.0},
            br: Point{x: width, y: height},
            bl: Point{x: 0.0,   y: height}
        }
    }
}


pub fn calculate_homography_matrix(s: &Quadrilateral, d: &Quadrilateral) -> HMatrix {
    let a = DMatrix::from_row_slice(8, 8, &[
        0.0,    0.0,    0.0, -s.tl.x, -s.tl.y, -1.0,  d.tl.y*s.tl.x,  d.tl.y*s.tl.y,
        s.tl.x, s.tl.y, 1.0,  0.0,     0.0,     0.0, -d.tl.x*s.tl.x, -d.tl.x*s.tl.y,
        0.0,    0.0,    0.0, -s.tr.x, -s.tr.y, -1.0,  d.tr.y*s.tr.x,  d.tr.y*s.tr.y,
        s.tr.x, s.tr.y, 1.0,  0.0,     0.0,     0.0, -d.tr.x*s.tr.x, -d.tr.x*s.tr.y,
        0.0,    0.0,    0.0, -s.br.x, -s.br.y, -1.0,  d.br.y*s.br.x,  d.br.y*s.br.y,
        s.br.x, s.br.y, 1.0,  0.0,     0.0,     0.0, -d.br.x*s.br.x, -d.br.x*s.br.y,
        0.0,    0.0,    0.0, -s.bl.x, -s.bl.y, -1.0,  d.bl.y*s.bl.x,  d.bl.y*s.bl.y,
        s.bl.x, s.bl.y, 1.0,  0.0,     0.0,     0.0, -d.bl.x*s.bl.x, -d.bl.x*s.bl.y,
    ]);

    let b = DVector::from_column_slice(&[
        -d.tl.y,
         d.tl.x,
        -d.tr.y,
         d.tr.x,
        -d.br.y,
         d.br.x,
        -d.bl.y,
         d.bl.x
    ]);

    let solution = a.lu().solve(&b).unwrap();
    let t = solution.as_slice();
    HMatrix{
        h00: t[0],
        h01: t[1],
        h02: t[2],
        h10: t[3],
        h11: t[4],
        h12: t[5],
        h20: t[6],
        h21: t[7],
        h22: 1f32,
    }
}


pub fn weight_cubic(p0: f32, p1: f32, p2: f32, p3: f32, w: f32) -> f32 {
    let value = p1 + 0.5 * w * (p2 - p0
        + w * (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3
        + w * (3.0 * (p1 - p2) + p3 - p0)));

    value.clamp(0.0, 255.0)
}


pub fn _pt(mut src: PixelBuffer, quad: Quadrilateral) -> Result<PixelBuffer, String> {
    let interleaved = src.interleaved;
    if interleaved {
        src.toggle_interleaved();
    }

    let out_dim = quad.output_dimension();
    let mut dst = PixelBuffer::blank(out_dim.0 as usize, out_dim.1 as usize, src.channels, false);
    let h = calculate_homography_matrix(&quad.dst_quad(), &quad);

    for channel in 0..dst.channels {
        let mut row = 0usize;
        let mut col = 0usize;

        let dst_off = channel*dst.height*dst.width;
        for dst_cell in &mut dst.data[dst_off..dst_off+dst.height*dst.width] {
            let sp = h.map(col as f32, row as f32);
            let x_weight = sp.x-sp.x.floor();
            let y_weight = sp.y-sp.y.floor();
            let (x, y) = (sp.x as usize, sp.y as usize);


            let mut kernel = [0f32; 16];
            let mut p: &[u8];
            let mut src_off = channel*src.height*src.width + (y-0)*src.width + (x-0);

            p = &src.data[src_off..src_off+4]; src_off += src.width;
            kernel[0] = p[0] as f32;
            kernel[1] = p[1] as f32;
            kernel[2] = p[2] as f32;
            kernel[3] = p[3] as f32;
            p = &src.data[src_off..src_off+4]; src_off += src.width;
            kernel[4] = p[0] as f32;
            kernel[5] = p[1] as f32;
            kernel[6] = p[2] as f32;
            kernel[7] = p[3] as f32;
            p = &src.data[src_off..src_off+4]; src_off += src.width;
            kernel[8] = p[0] as f32;
            kernel[9] = p[1] as f32;
            kernel[10] = p[2] as f32;
            kernel[11] = p[3] as f32;
            p = &src.data[src_off..src_off+4];
            kernel[12] = p[0] as f32;
            kernel[13] = p[1] as f32;
            kernel[14] = p[2] as f32;
            kernel[15] = p[3] as f32;

            let r0 = weight_cubic(kernel[0],  kernel[1],  kernel[2],  kernel[3],  x_weight);
            let r1 = weight_cubic(kernel[4],  kernel[5],  kernel[6],  kernel[7],  x_weight);
            let r2 = weight_cubic(kernel[8],  kernel[9],  kernel[10], kernel[11], x_weight);
            let r3 = weight_cubic(kernel[12], kernel[13], kernel[14], kernel[15], x_weight);

            *dst_cell = weight_cubic(r0, r1, r2, r3, y_weight) as u8;

            col += 1;
            if col >= dst.width {
                col = 0usize;
                row += 1;
            }
        }
    }



    if interleaved != dst.interleaved {
        dst.toggle_interleaved();
    }
    Ok(dst)
}

