![alt text|80](/images/AOP-networkFinder_for_paper.jpg)
Graphic mark of "AOP-networkFinder. Green represent Molecular Initiation Events (MIEs) in the Adverse Outcome Pathway (AOP). Orange represents adherent Key Events (KEs). Red triangles represent Adverse Outcomes (AOs), at the end of the path.
The arrows illustrate the direction of Key Events Relationships (KERs). Blue circles represent genes connected to KEs.
Notice that this representation is in form a Directed Acyclic Graph (DAG) with no directed cycles.


## Web-Application AOP-networkFinder is available under:
## https://aop-networkfinder.no/

Please cite the AOP-networkFinder:
BIORXIV/2024/591733  "AOP-networkFinder - A versatile and user-friendly tool for FAIR reconstruction of Adverse Outcome Pathway networks from the AOP-Wiki"
Authors: Nurettin Yarar, Marvin Martens, Torbjørn Rognes, Jan Lavender, Hubert Dirven, Karine Audouze and Marcin W. Wojewodzic#

Corresponding author: Marcin W. Wojewodzic (Email: maww [at] fhi.no)

Tool version v1 is also on Zenono at Computational Toxicology at Norwegian Institute of Public Health:
https://zenodo.org/records/11068434


1. Finds the status of all AOPs in the webpage AOPWiki.org/aops (OECD Status)


The Current GUI of the AOP_Visualizer webpage:

![main window](/images/Figures_AOP-network-finder_02032024-Figure1_Jan.jpg)


2. How to run the application locally using Docker

## Prerequisites
Docker installed on your system.

## Running the project locally
1. Clone the repository
2. Navigate to the project directory
3. Run the following command to build the Docker image:
```
 docker-compose up --build     
 ```
4. The application should be running on port 8000. If you change something in the the code should reload automatically. Just refresh the page in your browser and it should be updated.
5. To stop the application, run the following command:
```
docker-compose down
```


To access the application locally:
http://localhost:8000

You should see a window similar to this:

![main window](/images/AOPnetworkFinder_main_page.png)
