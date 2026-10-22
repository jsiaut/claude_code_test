"""Profil par échantillonnage d'une commande du pipeline (D-0072, point 3 c).

Un fil relève la pile du fil principal cent fois par seconde. Chaque relevé pèse le temps écoulé depuis le précédent,
pour qu'un appel C long qui garde la main ne soit pas sous-compté. Le rapport donne, pour les fonctions les plus
lourdes, le temps inclusif (la fonction est dans la pile) et le temps propre (elle est au sommet). Les processus fils
(pools) ne sont pas vus : leur durée revient à la fonction qui les attend.

    python -m pipeline.profiling work/tmp/profil.txt pipeline.assemble 2026-10-07 [--sans-cache]
"""
import collections
import runpy
import sys
import threading
import time


def frame_key(code):
    """Fonction d'un cadre : fichier relatif au dépôt (ou nom de la bibliothèque) et nom de la fonction."""
    f = code.co_filename
    for mark in ("/pipeline/", "/site-packages/", "/dist-packages/", "/lib/python3"):
        if mark in f:
            f = f.split(mark, 1)[1]
            break
    return f"{f}:{code.co_name}"


def report(incl, own, total, wall, top=45):
    lines = [f"temps total échantillonné : {total:.1f} s (horloge : {wall:.1f} s)", "", "inclusif :"]
    for k, v in incl.most_common(top):
        lines.append(f"  {v:9.1f} s {100 * v / total:5.1f} %  {k}")
    lines += ["", "propre :"]
    for k, v in own.most_common(top):
        lines.append(f"  {v:9.1f} s {100 * v / total:5.1f} %  {k}")
    return "\n".join(lines) + "\n"


def profile(out, module, args, hz=100):
    main_id = threading.get_ident()
    incl, own = collections.Counter(), collections.Counter()
    stop = threading.Event()
    state = {"last": time.perf_counter(), "total": 0.0}

    def sample():
        while not stop.wait(1 / hz):
            now = time.perf_counter()
            dt, state["last"] = now - state["last"], now
            f = sys._current_frames().get(main_id)
            if f is None:
                continue
            state["total"] += dt
            own[frame_key(f.f_code)] += dt
            seen = set()
            while f is not None:
                k = frame_key(f.f_code)
                if k not in seen:
                    incl[k] += dt
                    seen.add(k)
                f = f.f_back
    t0 = time.perf_counter()
    th = threading.Thread(target=sample, daemon=True)
    th.start()
    sys.argv = [module, *args]
    try:
        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit:
        pass
    finally:
        stop.set()
        th.join()
        text = report(incl, own, state["total"], time.perf_counter() - t0)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(text[:4000])


if __name__ == "__main__":
    profile(sys.argv[1], sys.argv[2], sys.argv[3:])
