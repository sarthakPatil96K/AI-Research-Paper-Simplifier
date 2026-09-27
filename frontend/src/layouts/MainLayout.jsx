import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import styles from "./MainLayout.module.css";

export default function MainLayout() {
  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}