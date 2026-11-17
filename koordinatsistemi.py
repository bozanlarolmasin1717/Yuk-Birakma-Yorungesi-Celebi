import math
from dataclasses import dataclass
from typing import Optional
import numpy as np

#ENU= 
# +x=east(doğu) 
# +y=north(kuzey) 
# +z= up (yukarı/irtifa) 
#g=9.81m/s^2


#yükün fiziksel ve aerodinamik özellikleri tutar.

@dataclass
class payloadParameters:
    mass: float
    cd: float
    cross_sectional_area:float

    def __post_init__(self):
        if self.mass <= 0:
            raise ValueError("Payload mass must be greater than zero.")
        if self.cd < 0:
            raise ValueError("Cd cannot be negative.")
        if self.cross_sectional_area <= 0:
            raise ValueError("Reference sectional area must be gerater than zero.")


#Ortam parametrelerini tutar.

@dataclass
class environmentParameters:
    g: float= 9.81
    rho_sea_level:float=1.225
    use_is: bool=False
    wind_speed:float=0.0
    wind_director:float=0.0
    wind_shear_coeff: float=0.0
    manual_wind_vector: Optional[np.ndarray]= None

    #verilen irtifadaki hava yoğunluğunu döndürür.
    def air_density(self, z:float):
        if not self.use_is:
            return self.rho_sea_level

        altitude= max(0.0,min(z,11000.0))
        temp=(288.15-0.0065* altitude)/288.15
        return self.rho_sea_level*(temp**4.25588)

    def wind_vector(self, z:float=0.0):
        if self.manual_wind_vector is not None:
            return np.asarray(self.manual_wind_vector,dtype=float)

        rad=math.radians(self.wind_director)
        effective_speed= self.wind_speed * (1.0 + self.wind_shear_coeff * max(0.0,z))
        wx= -effective_speed * math.sin(rad)
        wy= -effective_speed * math.cos(rad)
        return np.array([wx,wy,0.0], dtype=float)

# bırakma anındaki iha bilgilerini tutar.
@dataclass
class UavState:
     position: np.ndarray
     speed: float 
     heading: float=90.0
     flight_path_angle: float =0.0

     def __post_init__(self):
        self.position=np.asarray(self.position, dtype=float)
        if self.position.shape != (3,):
            raise ValueError("Position vector must be three element array.")
        if self.speed < 0:
            raise ValueError("Uav speed cannot be negative.")

     #yönelim ve uçuş yolu açılarına göre hesaplar.
     @property
     def initial_velocity(self):
        psi=math.radians(self.heading)
        gamma= math.radians(self.flight_path_angle)
        horizontal_speed= self.speed * math.cos(gamma)
        vx0=horizontal_speed * math.sin(psi)
        vy0=horizontal_speed * math.cos(psi)
        vz0=self.speed * math.sin(gamma)
        return np.array ([vx0,vy0,vz0], dtype=float )

#ileri balistik simülasyonunun çıktıları için
@dataclass
class simulationResult:
    impact_point: np.ndarray
    flight_time: float
    impact_velocity: np.ndarray
    trajectory: np.ndarray
    
    