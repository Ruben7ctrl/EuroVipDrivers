import React, { useEffect, useRef } from "react";
import "../styles/HeroShowcase.css";
import anime from "animejs";


// Importa tus imágenes de coches negros (las que ya tienes)
// Ajusta las rutas según tu estructura
import car1 from "../assets/eurovipdrivers/MercedesE.png";
import car2 from "../assets/eurovipdrivers/MercedesV.png";
import car3 from "../assets/eurovipdrivers/MercedesS.png";
import car4 from "../assets/eurovipdrivers/MercedesVito.png";

export default function HeroShowcase({ onBook }) {
    const cars = [car1, car2, car3, car4];
    const carRefs = useRef([]);

    const setRef = (el, idx) => {
        carRefs.current[idx] = el;
    };

    useEffect(() => {
        let cancelled = false;
        anime.set(carRefs.current, { translateX: "120vw", opacity: 0 });

        const playLoop = async () => {
            while (!cancelled) {
                for (const car of carRefs.current) {
                    const tl = anime.timeline();
                    tl.add({
                        targets: car,
                        translateX: ["120vw", "0vw"],
                        opacity: [0, 1],
                        duration: 900,
                        easing: "easeOutCubic",
                    })
                        .add({
                            targets: car,
                            translateX: ["0vw", "-2vw"],
                            duration: 1600,
                            easing: "linear",
                        })
                        .add({
                            targets: car,
                            translateX: ["-2vw", "-120vw"],
                            opacity: [1, 0],
                            duration: 900,
                            easing: "easeInCubic",
                        });

                    await tl.finished;
                    if (cancelled) break;
                }
            }
        };

        playLoop();
        return () => { cancelled = true; anime.remove(carRefs.current); };
    }, []);

    return (
        <section className="hero">
            <div className="hero__overlay" />

            <div className="hero__content">
                <h1 className="hero__title">EUROVIPDRIVERS</h1>
                <p className="hero__subtitle">Premium Taxi Services</p>
                <button className="ed-btn ed-btn--gold hero__cta" onClick={onBook}>Book Now</button>
            </div>

            <div className="hero__cars">
                {cars.map((src, i) => (
                    <img
                        key={i}
                        src={src}
                        alt={`Luxury car ${i + 1}`}
                        className="hero__car"
                        ref={(el) => setRef(el, i)}
                        draggable={false}
                    />
                ))}
            </div>
        </section>
    );
}