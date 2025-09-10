
import React, { useState } from "react";
import "../styles/fleet.css";
import userServices from "../services/userServices";
import FleetCarousel from "../components/FleetCarrusel";

export const Fleet = () => {


    const handleReserve = (car) => {
        // Por ejemplo: navigate(`/book?car=${car.id}`)
        console.log("Reservar:", car);
    };



    return (
        <div className="fondoMain d-flex justify-content-center align-items-center full-height">
            <FleetCarousel onReserve={handleReserve} />
        </div>
    );
}