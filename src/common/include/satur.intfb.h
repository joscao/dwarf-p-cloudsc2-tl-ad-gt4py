INTERFACE
SUBROUTINE SATUR ( KIDIA , KFDIA , KLON , KTDIA , KLEV, LDPHYLIN,&
 & PAPRSF, PT , PQSAT , KFLAG, YDCST, YDTHF ) 
USE PARKIND1 ,ONLY : JPIM ,JPRB
USE YOMCST   , ONLY : TOMCST
USE YOETHF   , ONLY : TOETHF
INTEGER(KIND=JPIM),INTENT(IN) :: KLON
INTEGER(KIND=JPIM),INTENT(IN) :: KLEV
INTEGER(KIND=JPIM),INTENT(IN) :: KIDIA
INTEGER(KIND=JPIM),INTENT(IN) :: KFDIA
INTEGER(KIND=JPIM),INTENT(IN) :: KTDIA
LOGICAL ,INTENT(IN) :: LDPHYLIN
REAL(KIND=JPRB) ,INTENT(IN) :: PAPRSF(KLON,KLEV)
REAL(KIND=JPRB) ,INTENT(IN) :: PT(KLON,KLEV)
REAL(KIND=JPRB) ,INTENT(OUT) :: PQSAT(KLON,KLEV)
INTEGER(KIND=JPIM),INTENT(IN) :: KFLAG
TYPE(TOMCST)                  :: YDCST
TYPE(TOETHF)                  :: YDTHF
END SUBROUTINE SATUR
END INTERFACE
