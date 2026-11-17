import math
from typing import Tuple
import numpy as np
from koordinatsistemi import(
    UavState,
    environmentParameters,
    payloadParameters,
    simulationResult,
)
###vakum balistiği çekirdeği

#hava direnci ve rüzgar yokken analitik uçuş süresini ve düşüş noktasını hesaplar.
def compute_vacum_ballistics(
        uav: UavState,
        env: environmentParameters,
        z_ground:float=0.0
):
    #başlangıç konumu ve ilk hız vektörünü alır.
    x0,y0,z0= uav.position
    vx0,vy0,vz0= uav.initial_velocity
    g= env.g
    
    #dikey hareket denkleminin uçuş süresini bulur.
    altitude_diff=z0 - z_ground
    discriminant= vz0**2 + 2.0*g*altitude_diff

    if discriminant <0:
        raise ValueError("Payload cannot reach target altitude with current vertical velocity.")
    t_flight= (vz0+math.sqrt(discriminant))/g

    #yatay hızlar sabit olduğu için düşüş koordinatlarını hesaplar.
    x_impact= x0+vx0* t_flight
    y_impact= y0+vy0* t_flight

    impact_point=np.array([x_impact, y_impact, z_ground], dtype= float)
    return impact_point, t_flight



###aerodinamik sürüklenme ve  rüzgar fizik motoru

def compute_acceleration(
        position: np.ndarray,
        velocity: np.ndarray,
        payload: payloadParameters,
        env: environmentParameters,
):

    # anlık irtifayı alıp rüzgr vektörünü ve bağıl hızı hesaplar.
    z=float(position[2])
    v_wind=env.wind_vector(z)
    v_rel= velocity -v_wind
    v_rel_magnitude= float(np.linalg.norm(v_rel))

    #aerodinamik sürüklenme ivmesini hesaplar.
    if payload.cd==0.0 or v_rel_magnitude==0.0:
        a_drag=np.zeros(3, dtype=float)
    else:
        rho= env.air_density(z)
        drag_factor=(0.5*rho*payload.cd*payload.cross_sectional_area)/ payload.mass
        a_drag= -drag_factor* v_rel_magnitude* v_rel

    #sürüklenme ivmesi ile yerçekimi ivmesini birleştirir.
    a_gravity= np.array([0.0,0.0, -env.g], dtype=float)
    total_acceleration= a_drag+ a_gravity

    return total_acceleration

###sayısal integrasyon ve zemin çarpışma çözücüsü
"""
RK4 sayısal integrasyon yöntemi ile yükün yörüngesini belirtir. z<= z_ground olduğunda doğrusal
interpolasyon ile kesin çarpışma koordinatını ve uçuş süresini hesaplar.
"""
def simulate_trajectory(
        uav=UavState,
        payload= payloadParameters,
        env=environmentParameters,
        dt: float=0.01,
        z_ground:float=0.0,
        record_trajectory:bool=True,
        max_time:float=600.0,
):

    if dt <=0:
        raise ValueError("dt must be greater than zero.")
    if uav.position[2]< z_ground:
        raise ValueError("Release altitude cannot be lower than ground elevation.")

    #başlangıç durum vektörü
    state=np.concatenate([uav.position, uav.initial_velocity])
    t=0.0
    trajectory_points=[state[:3].copy()] if record_trajectory else[]

    # durum vektörünün zamana göre türevini alır.
    def state_derivative(s: np.ndarray):
        pos= s[:3]
        vel=s[3:]
        acc=compute_acceleration(pos,vel,payload,env)
        return np.concatenate([vel,acc])

    #RK4
    max_steps= int(max_time/dt)
    for _ in range (max_steps):
        prev_state=state.copy()
        prev_t=t


        k1= state_derivative(state)
        k2= state_derivative(state+ 0.5*dt*k1)
        k3= state_derivative(state+0.5*dt*k2)
        k4= state_derivative(state+dt *k3)

        state= state+ (dt/6.0)* (k1+2.0*k2+ 2.0*k3+ k4)
        t += dt

        #zemin çarpışma kontrolü ve doğrusal interpolasyon 
        if state[2]<= z_ground:
            z_n=prev_state[2]
            z_n1= state[2]
            denom= z_n - z_n1
            alpha= (z_n - z_ground)/ denom if abs(denom) > 1e-15 else 0.0

            final_state= prev_state+alpha * (state -prev_state)
            final_state[2]= z_ground
            exact_flight_time= prev_t+ alpha *dt

            if record_trajectory:
                trajectory_points.append(final_state[:3].copy())

            return simulationResult(
                impact_point=final_state[:3],
                flight_time=exact_flight_time,
                impact_velocity=final_state[3:],
                trajectory= np.array(trajectory_points, dtype=float) if record_trajectory else np.empty((0,3)),
                )
        if record_trajectory:
            trajectory_points.append(state[:3].copy())
    raise RuntimeError("Maximum simulation time exceeded; payload did not reach ground.")


        