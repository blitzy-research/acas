-- MySQL dump 10.13  Distrib 8.0.37, for Linux (x86_64)
--
-- Host: localhost    Database: PAY_seed
-- ------------------------------------------------------
-- Server version	8.0.37

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `PAY_seed`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `PAY_USA_seed` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `PAY_USA_seed`;

--
-- Table structure for table `CHECK`
--

DROP TABLE IF EXISTS `CHECK`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CHECK` (
  `PRIMARY_KEY` int NOT NULL AUTO_INCREMENT,
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `ADJ_WORK_COMP` decimal(6,0) NOT NULL,
  `ADJ_DEPARTMENT` decimal(7,0) NOT NULL,
  `ADJ_STATE_NUM` decimal(2,0) NOT NULL,
  `ADJ_HOURS_REG` decimal(9,2) NOT NULL,
  `ADJ_HOURS_OT` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYA` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYB` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYC` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYD` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYE` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYF` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYG` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYH` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYI` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYJ` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYK` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYL` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYM` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYN` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_REG` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_OT` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYA` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYB` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYC` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYD` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYE` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYF` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYG` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYH` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYI` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYJ` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYK` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYL` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYM` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYN` decimal(9,2) NOT NULL,
  `ADJ_GROSS` decimal(9,2) NOT NULL,
  `ADJ_FWH` decimal(9,2) NOT NULL,
  `ADJ_FICA` decimal(9,2) NOT NULL,
  `ADJ_MCARE` decimal(9,2) NOT NULL,
  `ADJ_STATE` decimal(9,2) NOT NULL,
  `ADJ_SDI` decimal(9,2) NOT NULL,
  `ADJ_EIC` decimal(9,2) NOT NULL,
  `ADJ_LOCAL` decimal(9,2) DEFAULT NULL,
  `ADJ_DED01` decimal(9,2) NOT NULL,
  `ADJ_DED02` decimal(9,2) NOT NULL,
  `ADJ_DED03` decimal(9,2) NOT NULL,
  `ADJ_DED04` decimal(9,2) NOT NULL,
  `ADJ_DED05` decimal(9,2) NOT NULL,
  `ADJ_DED06` decimal(9,2) NOT NULL,
  `ADJ_DED07` decimal(9,2) NOT NULL,
  `ADJ_DED08` decimal(9,2) NOT NULL,
  `ADJ_DED09` decimal(9,2) NOT NULL,
  `ADJ_DED10` decimal(9,2) NOT NULL,
  `ADJ_DED11` decimal(9,2) NOT NULL,
  `ADJ_DED12` decimal(9,2) NOT NULL,
  `ADJ_DED13` decimal(9,2) NOT NULL,
  `ADJ_DED14` decimal(9,2) NOT NULL,
  `ADJ_DED15` decimal(9,2) NOT NULL,
  `ADJ_DED16` decimal(9,2) NOT NULL,
  `ADJ_NET` decimal(9,2) NOT NULL,
  `ADJ_FICA_US` decimal(9,2) NOT NULL,
  `ADJ_MCARE_US` decimal(9,2) NOT NULL,
  `ADJ_FUTA` decimal(9,2) NOT NULL,
  `ADJ_SUTA` decimal(9,2) NOT NULL,
  `ADJ_CHECK_NUMBER` decimal(6,0) NOT NULL,
  `ADJ_CHECK_DATE` date NOT NULL,
  `ADJ_CHECK_TYPE` char(2) NOT NULL,
  PRIMARY KEY (`PRIMARY_KEY`),
  KEY `EMP_NUMBER` (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Employee Check Records';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `COMAST`
--

DROP TABLE IF EXISTS `COMAST`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMAST` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_NAME` char(30) NOT NULL,
  `CO_ADDRESS_1` char(30) NOT NULL,
  `CO_ADDRESS_2` char(30) NOT NULL,
  `CO_ADDRESS_3` char(30) NOT NULL,
  `CO_STATE` char(2) NOT NULL,
  `CO_ZIP` decimal(5,0) NOT NULL,
  `CO_FEDERAL_ID` char(10) NOT NULL,
  `CO_STATE_ID` char(10) NOT NULL,
  `CO_DATE_ENDING` date NOT NULL,
  `CO_DATE_CHECK` date NOT NULL,
  `CO_CHECK_NUM` decimal(9,0) NOT NULL,
  `CO_OPTION_01` char(2) NOT NULL,
  `CO_OPTION_02` char(2) NOT NULL,
  `CO_OPTION_03` char(2) NOT NULL,
  `CO_OPTION_04` char(2) NOT NULL,
  `CO_OPTION_05` char(2) NOT NULL,
  `CO_OPTION_06` char(2) NOT NULL,
  `CO_OPTION_07` char(2) NOT NULL,
  `CO_OPTION_08` char(2) NOT NULL,
  `CO_OPTION_09` char(2) NOT NULL,
  `CO_OPTION_10` char(2) NOT NULL,
  `CO_TAKE_DED01` char(2) NOT NULL,
  `CO_TAKE_DED02` char(2) NOT NULL,
  `CO_TAKE_DED03` char(2) NOT NULL,
  `CO_TAKE_DED04` char(2) NOT NULL,
  `CO_TAKE_DED05` char(2) NOT NULL,
  `CO_TAKE_DED06` char(2) NOT NULL,
  `CO_TAKE_DED07` char(2) NOT NULL,
  `CO_TAKE_DED08` char(2) NOT NULL,
  `CO_TAKE_DED09` char(2) NOT NULL,
  `CO_TAKE_DED10` char(2) NOT NULL,
  `CO_TAKE_DED11` char(2) NOT NULL,
  `CO_TAKE_DED12` char(2) NOT NULL,
  `CO_TAKE_DED13` char(2) NOT NULL,
  `CO_TAKE_DED14` char(2) NOT NULL,
  `CO_TAKE_DED15` char(2) NOT NULL,
  `CO_TAKE_DED16` char(2) NOT NULL,
  `CO_FICA_MAX` decimal(9,2) NOT NULL,
  `CO_FICA_PERC` decimal(6,4) NOT NULL,
  `CO_MCARE_MAX` decimal(9,2) NOT NULL,
  `CO_MCARE_PERC` decimal(6,4) NOT NULL,
  `CO_FED_SHELTER` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FUTA_PERC` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FUTA_MAX` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_SUTA_PERC` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_SUTA_MAX` decimal(9,2) NOT NULL DEFAULT '0.00',
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `COMAST_DEDUCTIONS`
--

DROP TABLE IF EXISTS `COMAST_DEDUCTIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMAST_DEDUCTIONS` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_HEAD_DED01` char(10) NOT NULL,
  `CO_HEAD_DED02` char(10) NOT NULL,
  `CO_HEAD_DED03` char(10) NOT NULL,
  `CO_HEAD_DED04` char(10) NOT NULL,
  `CO_HEAD_DED05` char(10) NOT NULL,
  `CO_HEAD_DED06` char(10) NOT NULL,
  `CO_HEAD_DED07` char(10) NOT NULL,
  `CO_HEAD_DED08` char(10) NOT NULL,
  `CO_HEAD_DED09` char(10) NOT NULL,
  `CO_HEAD_DED10` char(10) NOT NULL,
  `CO_HEAD_DED11` char(10) NOT NULL,
  `CO_HEAD_DED12` char(10) NOT NULL,
  `CO_HEAD_DED13` char(10) NOT NULL,
  `CO_HEAD_DED14` char(10) NOT NULL,
  `CO_HEAD_DED15` char(10) NOT NULL,
  `CO_HEAD_DED16` char(10) NOT NULL,
  `CO_DED_KEY01` char(2) NOT NULL,
  `CO_DED_KEY02` char(2) NOT NULL,
  `CO_DED_KEY03` char(2) NOT NULL,
  `CO_DED_KEY04` char(2) NOT NULL,
  `CO_DED_KEY05` char(2) NOT NULL,
  `CO_DED_KEY06` char(2) NOT NULL,
  `CO_DED_KEY07` char(2) NOT NULL,
  `CO_DED_KEY08` char(2) NOT NULL,
  `CO_DED_KEY09` char(2) NOT NULL,
  `CO_DED_KEY10` char(2) NOT NULL,
  `CO_DED_KEY11` char(2) NOT NULL,
  `CO_DED_KEY12` char(2) NOT NULL,
  `CO_DED_KEY13` char(2) NOT NULL,
  `CO_DED_KEY14` char(2) NOT NULL,
  `CO_DED_KEY15` char(2) NOT NULL,
  `CO_DED_KEY16` char(2) NOT NULL,
  `CO_DEDAMT01` decimal(9,4) NOT NULL,
  `CO_DEDAMT02` decimal(9,4) NOT NULL,
  `CO_DEDAMT03` decimal(9,4) NOT NULL,
  `CO_DEDAMT04` decimal(9,4) NOT NULL,
  `CO_DEDAMT05` decimal(9,4) NOT NULL,
  `CO_DEDAMT06` decimal(9,4) NOT NULL,
  `CO_DEDAMT07` decimal(9,4) NOT NULL,
  `CO_DEDAMT08` decimal(9,4) NOT NULL,
  `CO_DEDAMT09` decimal(9,4) NOT NULL,
  `CO_DEDAMT10` decimal(9,4) NOT NULL,
  `CO_DEDAMT11` decimal(9,4) NOT NULL,
  `CO_DEDAMT12` decimal(9,4) NOT NULL,
  `CO_DEDAMT13` decimal(9,4) NOT NULL,
  `CO_DEDAMT14` decimal(9,4) NOT NULL,
  `CO_DEDAMT15` decimal(9,4) NOT NULL,
  `CO_DEDAMT16` decimal(9,4) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `COMAST_EIC_TAX`
--

DROP TABLE IF EXISTS `COMAST_EIC_TAX`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMAST_EIC_TAX` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_EIC_OVER01` decimal(9,2) NOT NULL,
  `CO_EIC_OVER02` decimal(9,2) NOT NULL,
  `CO_EIC_OVER03` decimal(9,2) NOT NULL,
  `CO_EIC_OVER04` decimal(9,2) NOT NULL,
  `CO_EIC_OVER05` decimal(9,2) NOT NULL,
  `CO_EIC_OVER06` decimal(9,2) NOT NULL,
  `CO_EIC_OVER07` decimal(9,2) NOT NULL,
  `CO_EIC_OVER08` decimal(9,2) NOT NULL,
  `CO_EIC_OVER09` decimal(9,2) NOT NULL,
  `CO_EIC_OVER10` decimal(9,2) NOT NULL,
  `CO_EIC_OVER11` decimal(9,2) NOT NULL,
  `CO_EIC_OVER12` decimal(9,2) NOT NULL,
  `CO_EIC_OVER13` decimal(9,2) NOT NULL,
  `CO_EIC_OVER14` decimal(9,2) NOT NULL,
  `CO_EIC_OVER15` decimal(9,2) NOT NULL,
  `CO_EIC_OVER16` decimal(9,2) NOT NULL,
  `CO_EIC_OVER17` decimal(9,2) NOT NULL,
  `CO_EIC_OVER18` decimal(9,2) NOT NULL,
  `CO_EIC_OVER19` decimal(9,2) NOT NULL,
  `CO_EIC_OVER20` decimal(9,2) NOT NULL,
  `CO_EIC_BASE01` decimal(9,2) NOT NULL,
  `CO_EIC_BASE02` decimal(9,2) NOT NULL,
  `CO_EIC_BASE03` decimal(9,2) NOT NULL,
  `CO_EIC_BASE04` decimal(9,2) NOT NULL,
  `CO_EIC_BASE05` decimal(9,2) NOT NULL,
  `CO_EIC_BASE06` decimal(9,2) NOT NULL,
  `CO_EIC_BASE07` decimal(9,2) NOT NULL,
  `CO_EIC_BASE08` decimal(9,2) NOT NULL,
  `CO_EIC_BASE09` decimal(9,2) NOT NULL,
  `CO_EIC_BASE10` decimal(9,2) NOT NULL,
  `CO_EIC_BASE11` decimal(9,2) NOT NULL,
  `CO_EIC_BASE12` decimal(9,2) NOT NULL,
  `CO_EIC_BASE13` decimal(9,2) NOT NULL,
  `CO_EIC_BASE14` decimal(9,2) NOT NULL,
  `CO_EIC_BASE15` decimal(9,2) NOT NULL,
  `CO_EIC_BASE16` decimal(9,2) NOT NULL,
  `CO_EIC_BASE17` decimal(9,2) NOT NULL,
  `CO_EIC_BASE18` decimal(9,2) NOT NULL,
  `CO_EIC_BASE19` decimal(9,2) NOT NULL,
  `CO_EIC_BASE20` decimal(9,2) NOT NULL,
  `CO_EIC_PERC01` decimal(6,4) NOT NULL,
  `CO_EIC_PERC02` decimal(6,4) NOT NULL,
  `CO_EIC_PERC03` decimal(6,4) NOT NULL,
  `CO_EIC_PERC04` decimal(6,4) NOT NULL,
  `CO_EIC_PERC05` decimal(6,4) NOT NULL,
  `CO_EIC_PERC06` decimal(6,4) NOT NULL,
  `CO_EIC_PERC07` decimal(6,4) NOT NULL,
  `CO_EIC_PERC08` decimal(6,4) NOT NULL,
  `CO_EIC_PERC09` decimal(6,4) NOT NULL,
  `CO_EIC_PERC10` decimal(6,4) NOT NULL,
  `CO_EIC_PERC11` decimal(6,4) NOT NULL,
  `CO_EIC_PERC12` decimal(6,4) NOT NULL,
  `CO_EIC_PERC13` decimal(6,4) NOT NULL,
  `CO_EIC_PERC14` decimal(6,4) NOT NULL,
  `CO_EIC_PERC15` decimal(6,4) NOT NULL,
  `CO_EIC_PERC16` decimal(6,4) NOT NULL,
  `CO_EIC_PERC17` decimal(6,4) NOT NULL,
  `CO_EIC_PERC18` decimal(6,4) NOT NULL,
  `CO_EIC_PERC19` decimal(6,4) NOT NULL,
  `CO_EIC_PERC20` decimal(6,4) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `COMAST_FED_TAX`
--

DROP TABLE IF EXISTS `COMAST_FED_TAX`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMAST_FED_TAX` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_FED_OVER01` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER02` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER03` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER04` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER05` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER06` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER07` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER08` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER09` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER10` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER11` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER12` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER13` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER14` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER15` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER16` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER17` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER18` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER19` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER20` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE01` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE02` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE03` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE04` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE05` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE06` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE07` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE08` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE09` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE10` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE11` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE12` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE13` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE14` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE15` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE16` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE17` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE18` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE19` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE20` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_PERC01` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC02` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC03` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC04` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC05` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC06` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC07` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC08` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC09` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC10` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC11` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC12` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC13` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC14` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC15` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC16` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC17` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC18` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC19` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC20` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `COMAST_PAY_TYPES`
--

DROP TABLE IF EXISTS `COMAST_PAY_TYPES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMAST_PAY_TYPES` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_REG_FLAG` char(12) NOT NULL,
  `CO_OT_FLAG` char(12) NOT NULL,
  `CO_PAYA_FLAG` char(12) NOT NULL,
  `CO_PAYB_FLAG` char(12) NOT NULL,
  `CO_PAYC_FLAG` char(12) NOT NULL,
  `CO_PAYD_FLAG` char(12) NOT NULL,
  `CO_PAYE_FLAG` char(12) NOT NULL,
  `CO_PAYF_FLAG` char(12) NOT NULL,
  `CO_PAYG_FLAG` char(12) NOT NULL,
  `CO_PAYH_FLAG` char(12) NOT NULL,
  `CO_PAYI_FLAG` char(12) NOT NULL,
  `CO_PAYJ_FLAG` char(12) NOT NULL,
  `CO_PAYK_FLAG` char(12) NOT NULL,
  `CO_PAYL_FLAG` char(12) NOT NULL,
  `CO_PAYM_FLAG` char(12) NOT NULL,
  `CO_PAYN_FLAG` char(12) NOT NULL,
  `CO_PAYA_HEAD` char(10) NOT NULL,
  `CO_PAYB_HEAD` char(10) NOT NULL,
  `CO_PAYC_HEAD` char(10) NOT NULL,
  `CO_PAYD_HEAD` char(10) NOT NULL,
  `CO_PAYE_HEAD` char(10) NOT NULL,
  `CO_PAYF_HEAD` char(10) NOT NULL,
  `CO_PAYG_HEAD` char(10) NOT NULL,
  `CO_PAYH_HEAD` char(10) NOT NULL,
  `CO_PAYI_HEAD` char(10) NOT NULL,
  `CO_PAYJ_HEAD` char(10) NOT NULL,
  `CO_PAYK_HEAD` char(10) NOT NULL,
  `CO_PAYL_HEAD` char(10) NOT NULL,
  `CO_PAYM_HEAD` char(10) NOT NULL,
  `CO_PAYN_HEAD` char(10) NOT NULL,
  `CO_RATE_REG` decimal(9,4) NOT NULL,
  `CO_RATE_OT` decimal(9,4) NOT NULL,
  `CO_RATE_PAYA` decimal(9,4) NOT NULL,
  `CO_RATE_PAYB` decimal(9,4) NOT NULL,
  `CO_RATE_PAYC` decimal(9,4) NOT NULL,
  `CO_RATE_PAYD` decimal(9,4) NOT NULL,
  `CO_RATE_PAYE` decimal(9,4) NOT NULL,
  `CO_RATE_PAYF` decimal(9,4) NOT NULL,
  `CO_RATE_PAYG` decimal(9,4) NOT NULL,
  `CO_RATE_PAYH` decimal(9,4) NOT NULL,
  `CO_RATE_PAYI` decimal(9,4) NOT NULL,
  `CO_RATE_PAYJ` decimal(9,4) NOT NULL,
  `CO_RATE_PAYK` decimal(9,4) NOT NULL,
  `CO_RATE_PAYL` decimal(9,4) NOT NULL,
  `CO_RATE_PAYM` decimal(9,4) NOT NULL,
  `CO_RATE_PAYN` decimal(9,4) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DEDUCT`
--

DROP TABLE IF EXISTS `DEDUCT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DEDUCT` (
  `PRIMARY_KEY` int NOT NULL AUTO_INCREMENT,
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `ONE_AMOUNT01` decimal(9,2) NOT NULL,
  `ONE_AMOUNT02` decimal(9,2) NOT NULL,
  `ONE_AMOUNT03` decimal(9,2) NOT NULL,
  `ONE_AMOUNT04` decimal(9,2) NOT NULL,
  `ONE_AMOUNT05` decimal(9,2) NOT NULL,
  `ONE_AMOUNT06` decimal(9,2) NOT NULL,
  `ONE_AMOUNT07` decimal(9,2) NOT NULL,
  `ONE_AMOUNT08` decimal(9,2) NOT NULL,
  `ONE_AMOUNT09` decimal(9,2) NOT NULL,
  `ONE_AMOUNT10` decimal(9,2) NOT NULL,
  `ONE_AMOUNT11` decimal(9,2) NOT NULL,
  `ONE_AMOUNT12` decimal(9,2) NOT NULL,
  `ONE_AMOUNT13` decimal(9,2) NOT NULL,
  `ONE_AMOUNT14` decimal(9,2) NOT NULL,
  `ONE_AMOUNT15` decimal(9,2) NOT NULL,
  `ONE_AMOUNT16` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT01` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT02` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT03` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT04` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT05` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT06` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT07` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT08` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT09` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT10` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT11` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT12` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT13` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT14` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT15` decimal(9,2) NOT NULL,
  `ONE_BAL_AMOUNT16` decimal(9,2) NOT NULL,
  `ONE_CHECK` decimal(6,0) NOT NULL,
  PRIMARY KEY (`PRIMARY_KEY`),
  KEY `EMP_NUMBER` (`EMP_NUMBER`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='One-Time Deductions';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DEPARTMENT`
--

DROP TABLE IF EXISTS `DEPARTMENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DEPARTMENT` (
  `DEPARTMENT_NUMBER` decimal(7,0) NOT NULL,
  `DEPARTMENT_NAME` char(30) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`DEPARTMENT_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMPLOYEE`
--

DROP TABLE IF EXISTS `EMPLOYEE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EMPLOYEE` (
  `EMP_NUMBER` decimal(6,0) NOT NULL DEFAULT '0',
  `EMP_NAME` char(30) NOT NULL,
  `EMP_ADDRESS_1` char(30) NOT NULL,
  `EMP_ADDRESS_2` char(30) NOT NULL,
  `EMP_ADDRESS_3` char(30) NOT NULL,
  `EMP_STATE` char(2) NOT NULL,
  `EMP_ZIP` decimal(5,0) NOT NULL,
  `EMP_WORK_COMP` decimal(6,0) NOT NULL,
  `EMP_DEPARTMENT` decimal(7,0) NOT NULL,
  `EMP_STATE_NUM` decimal(2,0) NOT NULL,
  `EMP_DDA_NUM` char(10) NOT NULL,
  `EMP_SSA_NUM` decimal(9,0) NOT NULL,
  `EMP_FED_MARITAL` char(2) NOT NULL,
  `EMP_ST_MARITAL` char(2) NOT NULL,
  `EMP_EIC_MARITAL` char(2) NOT NULL,
  `EMP_FED_NUM_DEP` decimal(2,0) NOT NULL,
  `EMP_ST_NUM_DEP` decimal(2,0) NOT NULL,
  `EMP_PAY_TYPE` char(2) NOT NULL,
  `EMP_STATUS` char(2) NOT NULL,
  `EMP_PAY_PERIOD` char(2) NOT NULL,
  `EMP_RATE_REG` decimal(9,4) NOT NULL,
  `EMP_RATE_OT` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYA` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYB` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYC` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYD` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYE` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYF` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYG` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYH` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYI` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYJ` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYK` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYL` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYM` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYN` decimal(9,4) NOT NULL,
  `EMP_FED_FLAG` char(2) NOT NULL,
  `EMP_FED_AMT` decimal(9,4) NOT NULL,
  `EMP_ST_FLAG` char(2) NOT NULL,
  `EMP_ST_AMT` decimal(9,4) NOT NULL,
  `EMP_DATE_LAST` date NOT NULL,
  `EMP_DATE_HIRE` date NOT NULL,
  `EMP_DATE_VACN` date NOT NULL,
  `EMP_DATE_1` date NOT NULL,
  `EMP_DATE_2` date NOT NULL,
  `EMP_FLAGS01` char(2) NOT NULL,
  `EMP_FLAGS02` char(2) NOT NULL,
  `EMP_FLAGS03` char(2) NOT NULL,
  `EMP_FLAGS04` char(2) NOT NULL,
  `EMP_FLAGS05` char(2) NOT NULL,
  `EMP_FLAGS06` char(2) NOT NULL,
  `EMP_FLAGS07` char(2) NOT NULL,
  `EMP_FLAGS08` char(2) NOT NULL,
  `EMP_FLAGS09` char(2) NOT NULL,
  `EMP_FLAGS10` char(2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Employee Default Deductions';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMPLOYEE_AUX`
--

DROP TABLE IF EXISTS `EMPLOYEE_AUX`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EMPLOYEE_AUX` (
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `EMP_NO_ROUTING_1` decimal(9,0) NOT NULL,
  `EMP_NO_ROUTING_2` decimal(9,0) NOT NULL,
  `EMP_NO_ACCOUNT_1` char(20) NOT NULL,
  `EMP_NO_ACCOUNT_2` char(20) NOT NULL,
  `EMP_TY_ACCOUNT_1` char(10) NOT NULL,
  `EMP_TY_ACCOUNT_2` char(10) NOT NULL,
  `EMP_FLAGS01` char(2) NOT NULL,
  `EMP_FLAGS02` char(2) NOT NULL,
  `EMP_FLAGS03` char(2) NOT NULL,
  `EMP_FLAGS04` char(2) NOT NULL,
  `EMP_FLAGS05` char(2) NOT NULL,
  `EMP_FLAGS06` char(2) NOT NULL,
  `EMP_FLAGS07` char(2) NOT NULL,
  `EMP_FLAGS08` char(2) NOT NULL,
  `EMP_FLAGS09` char(2) NOT NULL,
  `EMP_FLAGS10` char(2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMPLOYEE_DEDUCTIONS`
--

DROP TABLE IF EXISTS `EMPLOYEE_DEDUCTIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EMPLOYEE_DEDUCTIONS` (
  `EMP_NUMBER` decimal(6,0) NOT NULL DEFAULT '0',
  `EMP_DED_KEY01` char(2) NOT NULL,
  `EMP_DED_KEY02` char(2) NOT NULL,
  `EMP_DED_KEY03` char(2) NOT NULL,
  `EMP_DED_KEY04` char(2) NOT NULL,
  `EMP_DED_KEY05` char(2) NOT NULL,
  `EMP_DED_KEY06` char(2) NOT NULL,
  `EMP_DED_KEY07` char(2) NOT NULL,
  `EMP_DED_KEY08` char(2) NOT NULL,
  `EMP_DED_KEY09` char(2) NOT NULL,
  `EMP_DED_KEY10` char(2) NOT NULL,
  `EMP_DED_KEY11` char(2) NOT NULL,
  `EMP_DED_KEY12` char(2) NOT NULL,
  `EMP_DED_KEY13` char(2) NOT NULL,
  `EMP_DED_KEY14` char(2) NOT NULL,
  `EMP_DED_KEY15` char(2) NOT NULL,
  `EMP_DED_KEY16` char(2) NOT NULL,
  `EMP_DED_AMOUNT01` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT02` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT03` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT04` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT05` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT06` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT07` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT08` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT09` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT10` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT11` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT12` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT13` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT14` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT15` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT16` decimal(9,4) NOT NULL,
  `EMP_BAL_AMOUNT01` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT02` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT03` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT04` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT05` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT06` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT07` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT08` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT09` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT10` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT11` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT12` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT13` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT14` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT15` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT16` decimal(9,2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Employee Default Deductions';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_CHECK`
--

DROP TABLE IF EXISTS `HISTORY_CHECK`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_CHECK` (
  `RECORD_NUMBER` int NOT NULL,
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `ADJ_WORK_COMP` decimal(6,0) NOT NULL,
  `ADJ_DEPARTMENT` decimal(7,0) NOT NULL,
  `ADJ_STATE_NUM` decimal(2,0) NOT NULL,
  `ADJ_HOURS_REG` decimal(9,2) NOT NULL,
  `ADJ_HOURS_OT` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYA` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYB` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYC` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYD` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYE` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYF` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYG` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYH` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYI` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYJ` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYK` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYL` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYM` decimal(9,2) NOT NULL,
  `ADJ_HOURS_PAYN` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_REG` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_OT` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYA` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYB` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYC` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYD` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYE` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYF` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYG` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYH` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYI` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYJ` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYK` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYL` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYM` decimal(9,2) NOT NULL,
  `ADJ_AMOUNT_PAYN` decimal(9,2) NOT NULL,
  `ADJ_GROSS` decimal(9,2) NOT NULL,
  `ADJ_FWH` decimal(9,2) NOT NULL,
  `ADJ_FICA` decimal(9,2) NOT NULL,
  `ADJ_MCARE` decimal(9,2) NOT NULL,
  `ADJ_STATE` decimal(9,2) NOT NULL,
  `ADJ_SDI` decimal(9,2) NOT NULL,
  `ADJ_EIC` decimal(9,2) NOT NULL,
  `ADJ_LOCAL` decimal(9,2) DEFAULT NULL,
  `ADJ_DED01` decimal(9,2) NOT NULL,
  `ADJ_DED02` decimal(9,2) NOT NULL,
  `ADJ_DED03` decimal(9,2) NOT NULL,
  `ADJ_DED04` decimal(9,2) NOT NULL,
  `ADJ_DED05` decimal(9,2) NOT NULL,
  `ADJ_DED06` decimal(9,2) NOT NULL,
  `ADJ_DED07` decimal(9,2) NOT NULL,
  `ADJ_DED08` decimal(9,2) NOT NULL,
  `ADJ_DED09` decimal(9,2) NOT NULL,
  `ADJ_DED10` decimal(9,2) NOT NULL,
  `ADJ_DED11` decimal(9,2) NOT NULL,
  `ADJ_DED12` decimal(9,2) NOT NULL,
  `ADJ_DED13` decimal(9,2) NOT NULL,
  `ADJ_DED14` decimal(9,2) NOT NULL,
  `ADJ_DED15` decimal(9,2) NOT NULL,
  `ADJ_DED16` decimal(9,2) NOT NULL,
  `ADJ_NET` decimal(9,2) NOT NULL,
  `ADJ_FICA_US` decimal(9,2) NOT NULL,
  `ADJ_MCARE_US` decimal(9,2) NOT NULL,
  `ADJ_FUTA` decimal(9,2) NOT NULL,
  `ADJ_SUTA` decimal(9,2) NOT NULL,
  `ADJ_CHECK_NUMBER` decimal(6,0) NOT NULL,
  `ADJ_CHECK_DATE` date NOT NULL,
  `ADJ_CHECK_TYPE` char(2) NOT NULL,
  KEY `EMP_NUMBER` (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_COMAST`
--

DROP TABLE IF EXISTS `HISTORY_COMAST`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_COMAST` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_NAME` char(30) NOT NULL,
  `CO_ADDRESS_1` char(30) NOT NULL,
  `CO_ADDRESS_2` char(30) NOT NULL,
  `CO_ADDRESS_3` char(30) NOT NULL,
  `CO_STATE` char(2) NOT NULL,
  `CO_ZIP` decimal(5,0) NOT NULL,
  `CO_FEDERAL_ID` char(10) NOT NULL,
  `CO_STATE_ID` char(10) NOT NULL,
  `CO_DATE_ENDING` date NOT NULL,
  `CO_DATE_CHECK` date NOT NULL,
  `CO_CHECK_NUM` decimal(9,0) NOT NULL,
  `CO_OPTION_01` char(2) NOT NULL,
  `CO_OPTION_02` char(2) NOT NULL,
  `CO_OPTION_03` char(2) NOT NULL,
  `CO_OPTION_04` char(2) NOT NULL,
  `CO_OPTION_05` char(2) NOT NULL,
  `CO_OPTION_06` char(2) NOT NULL,
  `CO_OPTION_07` char(2) NOT NULL,
  `CO_OPTION_08` char(2) NOT NULL,
  `CO_OPTION_09` char(2) NOT NULL,
  `CO_OPTION_10` char(2) NOT NULL,
  `CO_TAKE_DED01` char(2) NOT NULL,
  `CO_TAKE_DED02` char(2) NOT NULL,
  `CO_TAKE_DED03` char(2) NOT NULL,
  `CO_TAKE_DED04` char(2) NOT NULL,
  `CO_TAKE_DED05` char(2) NOT NULL,
  `CO_TAKE_DED06` char(2) NOT NULL,
  `CO_TAKE_DED07` char(2) NOT NULL,
  `CO_TAKE_DED08` char(2) NOT NULL,
  `CO_TAKE_DED09` char(2) NOT NULL,
  `CO_TAKE_DED10` char(2) NOT NULL,
  `CO_TAKE_DED11` char(2) NOT NULL,
  `CO_TAKE_DED12` char(2) NOT NULL,
  `CO_TAKE_DED13` char(2) NOT NULL,
  `CO_TAKE_DED14` char(2) NOT NULL,
  `CO_TAKE_DED15` char(2) NOT NULL,
  `CO_TAKE_DED16` char(2) NOT NULL,
  `CO_FICA_MAX` decimal(9,2) NOT NULL,
  `CO_FICA_PERC` decimal(6,4) NOT NULL,
  `CO_MCARE_MAX` decimal(9,2) NOT NULL,
  `CO_MCARE_PERC` decimal(6,4) NOT NULL,
  `CO_FED_SHELTER` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FUTA_PERC` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FUTA_MAX` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_SUTA_PERC` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_SUTA_MAX` decimal(9,2) NOT NULL DEFAULT '0.00',
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `CO_NUMBER` (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_COMAST_DEDUCTIONS`
--

DROP TABLE IF EXISTS `HISTORY_COMAST_DEDUCTIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_COMAST_DEDUCTIONS` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_HEAD_DED01` char(10) NOT NULL,
  `CO_HEAD_DED02` char(10) NOT NULL,
  `CO_HEAD_DED03` char(10) NOT NULL,
  `CO_HEAD_DED04` char(10) NOT NULL,
  `CO_HEAD_DED05` char(10) NOT NULL,
  `CO_HEAD_DED06` char(10) NOT NULL,
  `CO_HEAD_DED07` char(10) NOT NULL,
  `CO_HEAD_DED08` char(10) NOT NULL,
  `CO_HEAD_DED09` char(10) NOT NULL,
  `CO_HEAD_DED10` char(10) NOT NULL,
  `CO_HEAD_DED11` char(10) NOT NULL,
  `CO_HEAD_DED12` char(10) NOT NULL,
  `CO_HEAD_DED13` char(10) NOT NULL,
  `CO_HEAD_DED14` char(10) NOT NULL,
  `CO_HEAD_DED15` char(10) NOT NULL,
  `CO_HEAD_DED16` char(10) NOT NULL,
  `CO_DED_KEY01` char(2) NOT NULL,
  `CO_DED_KEY02` char(2) NOT NULL,
  `CO_DED_KEY03` char(2) NOT NULL,
  `CO_DED_KEY04` char(2) NOT NULL,
  `CO_DED_KEY05` char(2) NOT NULL,
  `CO_DED_KEY06` char(2) NOT NULL,
  `CO_DED_KEY07` char(2) NOT NULL,
  `CO_DED_KEY08` char(2) NOT NULL,
  `CO_DED_KEY09` char(2) NOT NULL,
  `CO_DED_KEY10` char(2) NOT NULL,
  `CO_DED_KEY11` char(2) NOT NULL,
  `CO_DED_KEY12` char(2) NOT NULL,
  `CO_DED_KEY13` char(2) NOT NULL,
  `CO_DED_KEY14` char(2) NOT NULL,
  `CO_DED_KEY15` char(2) NOT NULL,
  `CO_DED_KEY16` char(2) NOT NULL,
  `CO_DEDAMT01` decimal(9,4) NOT NULL,
  `CO_DEDAMT02` decimal(9,4) NOT NULL,
  `CO_DEDAMT03` decimal(9,4) NOT NULL,
  `CO_DEDAMT04` decimal(9,4) NOT NULL,
  `CO_DEDAMT05` decimal(9,4) NOT NULL,
  `CO_DEDAMT06` decimal(9,4) NOT NULL,
  `CO_DEDAMT07` decimal(9,4) NOT NULL,
  `CO_DEDAMT08` decimal(9,4) NOT NULL,
  `CO_DEDAMT09` decimal(9,4) NOT NULL,
  `CO_DEDAMT10` decimal(9,4) NOT NULL,
  `CO_DEDAMT11` decimal(9,4) NOT NULL,
  `CO_DEDAMT12` decimal(9,4) NOT NULL,
  `CO_DEDAMT13` decimal(9,4) NOT NULL,
  `CO_DEDAMT14` decimal(9,4) NOT NULL,
  `CO_DEDAMT15` decimal(9,4) NOT NULL,
  `CO_DEDAMT16` decimal(9,4) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `CO_NUMBER` (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_COMAST_EIC_TAX`
--

DROP TABLE IF EXISTS `HISTORY_COMAST_EIC_TAX`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_COMAST_EIC_TAX` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_EIC_OVER01` decimal(9,2) NOT NULL,
  `CO_EIC_OVER02` decimal(9,2) NOT NULL,
  `CO_EIC_OVER03` decimal(9,2) NOT NULL,
  `CO_EIC_OVER04` decimal(9,2) NOT NULL,
  `CO_EIC_OVER05` decimal(9,2) NOT NULL,
  `CO_EIC_OVER06` decimal(9,2) NOT NULL,
  `CO_EIC_OVER07` decimal(9,2) NOT NULL,
  `CO_EIC_OVER08` decimal(9,2) NOT NULL,
  `CO_EIC_OVER09` decimal(9,2) NOT NULL,
  `CO_EIC_OVER10` decimal(9,2) NOT NULL,
  `CO_EIC_OVER11` decimal(9,2) NOT NULL,
  `CO_EIC_OVER12` decimal(9,2) NOT NULL,
  `CO_EIC_OVER13` decimal(9,2) NOT NULL,
  `CO_EIC_OVER14` decimal(9,2) NOT NULL,
  `CO_EIC_OVER15` decimal(9,2) NOT NULL,
  `CO_EIC_OVER16` decimal(9,2) NOT NULL,
  `CO_EIC_OVER17` decimal(9,2) NOT NULL,
  `CO_EIC_OVER18` decimal(9,2) NOT NULL,
  `CO_EIC_OVER19` decimal(9,2) NOT NULL,
  `CO_EIC_OVER20` decimal(9,2) NOT NULL,
  `CO_EIC_BASE01` decimal(9,2) NOT NULL,
  `CO_EIC_BASE02` decimal(9,2) NOT NULL,
  `CO_EIC_BASE03` decimal(9,2) NOT NULL,
  `CO_EIC_BASE04` decimal(9,2) NOT NULL,
  `CO_EIC_BASE05` decimal(9,2) NOT NULL,
  `CO_EIC_BASE06` decimal(9,2) NOT NULL,
  `CO_EIC_BASE07` decimal(9,2) NOT NULL,
  `CO_EIC_BASE08` decimal(9,2) NOT NULL,
  `CO_EIC_BASE09` decimal(9,2) NOT NULL,
  `CO_EIC_BASE10` decimal(9,2) NOT NULL,
  `CO_EIC_BASE11` decimal(9,2) NOT NULL,
  `CO_EIC_BASE12` decimal(9,2) NOT NULL,
  `CO_EIC_BASE13` decimal(9,2) NOT NULL,
  `CO_EIC_BASE14` decimal(9,2) NOT NULL,
  `CO_EIC_BASE15` decimal(9,2) NOT NULL,
  `CO_EIC_BASE16` decimal(9,2) NOT NULL,
  `CO_EIC_BASE17` decimal(9,2) NOT NULL,
  `CO_EIC_BASE18` decimal(9,2) NOT NULL,
  `CO_EIC_BASE19` decimal(9,2) NOT NULL,
  `CO_EIC_BASE20` decimal(9,2) NOT NULL,
  `CO_EIC_PERC01` decimal(6,4) NOT NULL,
  `CO_EIC_PERC02` decimal(6,4) NOT NULL,
  `CO_EIC_PERC03` decimal(6,4) NOT NULL,
  `CO_EIC_PERC04` decimal(6,4) NOT NULL,
  `CO_EIC_PERC05` decimal(6,4) NOT NULL,
  `CO_EIC_PERC06` decimal(6,4) NOT NULL,
  `CO_EIC_PERC07` decimal(6,4) NOT NULL,
  `CO_EIC_PERC08` decimal(6,4) NOT NULL,
  `CO_EIC_PERC09` decimal(6,4) NOT NULL,
  `CO_EIC_PERC10` decimal(6,4) NOT NULL,
  `CO_EIC_PERC11` decimal(6,4) NOT NULL,
  `CO_EIC_PERC12` decimal(6,4) NOT NULL,
  `CO_EIC_PERC13` decimal(6,4) NOT NULL,
  `CO_EIC_PERC14` decimal(6,4) NOT NULL,
  `CO_EIC_PERC15` decimal(6,4) NOT NULL,
  `CO_EIC_PERC16` decimal(6,4) NOT NULL,
  `CO_EIC_PERC17` decimal(6,4) NOT NULL,
  `CO_EIC_PERC18` decimal(6,4) NOT NULL,
  `CO_EIC_PERC19` decimal(6,4) NOT NULL,
  `CO_EIC_PERC20` decimal(6,4) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `CO_NUMBER` (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_COMAST_FED_TAX`
--

DROP TABLE IF EXISTS `HISTORY_COMAST_FED_TAX`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_COMAST_FED_TAX` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_FED_OVER01` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER02` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER03` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER04` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER05` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER06` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER07` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER08` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER09` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER10` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER11` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER12` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER13` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER14` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER15` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER16` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER17` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER18` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER19` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_OVER20` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE01` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE02` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE03` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE04` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE05` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE06` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE07` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE08` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE09` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE10` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE11` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE12` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE13` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE14` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE15` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE16` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE17` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE18` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE19` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_BASE20` decimal(9,2) NOT NULL DEFAULT '0.00',
  `CO_FED_PERC01` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC02` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC03` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC04` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC05` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC06` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC07` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC08` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC09` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC10` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC11` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC12` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC13` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC14` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC15` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC16` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC17` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC18` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC19` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `CO_FED_PERC20` decimal(6,4) NOT NULL DEFAULT '0.0000',
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `CO_NUMBER` (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_COMAST_PAY_TYPES`
--

DROP TABLE IF EXISTS `HISTORY_COMAST_PAY_TYPES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_COMAST_PAY_TYPES` (
  `CO_NUMBER` decimal(3,0) NOT NULL,
  `CO_REG_FLAG` char(12) NOT NULL,
  `CO_OT_FLAG` char(12) NOT NULL,
  `CO_PAYA_FLAG` char(12) NOT NULL,
  `CO_PAYB_FLAG` char(12) NOT NULL,
  `CO_PAYC_FLAG` char(12) NOT NULL,
  `CO_PAYD_FLAG` char(12) NOT NULL,
  `CO_PAYE_FLAG` char(12) NOT NULL,
  `CO_PAYF_FLAG` char(12) NOT NULL,
  `CO_PAYG_FLAG` char(12) NOT NULL,
  `CO_PAYH_FLAG` char(12) NOT NULL,
  `CO_PAYI_FLAG` char(12) NOT NULL,
  `CO_PAYJ_FLAG` char(12) NOT NULL,
  `CO_PAYK_FLAG` char(12) NOT NULL,
  `CO_PAYL_FLAG` char(12) NOT NULL,
  `CO_PAYM_FLAG` char(12) NOT NULL,
  `CO_PAYN_FLAG` char(12) NOT NULL,
  `CO_PAYA_HEAD` char(10) NOT NULL,
  `CO_PAYB_HEAD` char(10) NOT NULL,
  `CO_PAYC_HEAD` char(10) NOT NULL,
  `CO_PAYD_HEAD` char(10) NOT NULL,
  `CO_PAYE_HEAD` char(10) NOT NULL,
  `CO_PAYF_HEAD` char(10) NOT NULL,
  `CO_PAYG_HEAD` char(10) NOT NULL,
  `CO_PAYH_HEAD` char(10) NOT NULL,
  `CO_PAYI_HEAD` char(10) NOT NULL,
  `CO_PAYJ_HEAD` char(10) NOT NULL,
  `CO_PAYK_HEAD` char(10) NOT NULL,
  `CO_PAYL_HEAD` char(10) NOT NULL,
  `CO_PAYM_HEAD` char(10) NOT NULL,
  `CO_PAYN_HEAD` char(10) NOT NULL,
  `CO_RATE_REG` decimal(9,4) NOT NULL,
  `CO_RATE_OT` decimal(9,4) NOT NULL,
  `CO_RATE_PAYA` decimal(9,4) NOT NULL,
  `CO_RATE_PAYB` decimal(9,4) NOT NULL,
  `CO_RATE_PAYC` decimal(9,4) NOT NULL,
  `CO_RATE_PAYD` decimal(9,4) NOT NULL,
  `CO_RATE_PAYE` decimal(9,4) NOT NULL,
  `CO_RATE_PAYF` decimal(9,4) NOT NULL,
  `CO_RATE_PAYG` decimal(9,4) NOT NULL,
  `CO_RATE_PAYH` decimal(9,4) NOT NULL,
  `CO_RATE_PAYI` decimal(9,4) NOT NULL,
  `CO_RATE_PAYJ` decimal(9,4) NOT NULL,
  `CO_RATE_PAYK` decimal(9,4) NOT NULL,
  `CO_RATE_PAYL` decimal(9,4) NOT NULL,
  `CO_RATE_PAYM` decimal(9,4) NOT NULL,
  `CO_RATE_PAYN` decimal(9,4) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `CO_NUMBER` (`CO_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Company Master';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_DEPARTMENT`
--

DROP TABLE IF EXISTS `HISTORY_DEPARTMENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_DEPARTMENT` (
  `DEPARTMENT_NUMBER` decimal(7,0) NOT NULL,
  `DEPARTMENT_NAME` char(30) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `DEPARTMENT_NUMBER` (`DEPARTMENT_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_EMPLOYEE`
--

DROP TABLE IF EXISTS `HISTORY_EMPLOYEE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_EMPLOYEE` (
  `EMP_NUMBER` decimal(6,0) NOT NULL DEFAULT '0',
  `EMP_NAME` char(30) NOT NULL,
  `EMP_ADDRESS_1` char(30) NOT NULL,
  `EMP_ADDRESS_2` char(30) NOT NULL,
  `EMP_ADDRESS_3` char(30) NOT NULL,
  `EMP_STATE` char(2) NOT NULL,
  `EMP_ZIP` decimal(5,0) NOT NULL,
  `EMP_WORK_COMP` decimal(6,0) NOT NULL,
  `EMP_DEPARTMENT` decimal(7,0) NOT NULL,
  `EMP_STATE_NUM` decimal(2,0) NOT NULL,
  `EMP_DDA_NUM` char(10) NOT NULL,
  `EMP_SSA_NUM` decimal(9,0) NOT NULL,
  `EMP_FED_MARITAL` char(2) NOT NULL,
  `EMP_ST_MARITAL` char(2) NOT NULL,
  `EMP_EIC_MARITAL` char(2) NOT NULL,
  `EMP_FED_NUM_DEP` decimal(2,0) NOT NULL,
  `EMP_ST_NUM_DEP` decimal(2,0) NOT NULL,
  `EMP_PAY_TYPE` char(2) NOT NULL,
  `EMP_STATUS` char(2) NOT NULL,
  `EMP_PAY_PERIOD` char(2) NOT NULL,
  `EMP_RATE_REG` decimal(9,4) NOT NULL,
  `EMP_RATE_OT` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYA` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYB` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYC` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYD` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYE` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYF` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYG` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYH` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYI` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYJ` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYK` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYL` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYM` decimal(9,4) NOT NULL,
  `EMP_RATE_PAYN` decimal(9,4) NOT NULL,
  `EMP_FED_FLAG` char(2) NOT NULL,
  `EMP_FED_AMT` decimal(9,4) NOT NULL,
  `EMP_ST_FLAG` char(2) NOT NULL,
  `EMP_ST_AMT` decimal(9,4) NOT NULL,
  `EMP_DATE_LAST` date NOT NULL,
  `EMP_DATE_HIRE` date NOT NULL,
  `EMP_DATE_VACN` date NOT NULL,
  `EMP_DATE_1` date NOT NULL,
  `EMP_DATE_2` date NOT NULL,
  `EMP_FLAGS01` char(2) NOT NULL,
  `EMP_FLAGS02` char(2) NOT NULL,
  `EMP_FLAGS03` char(2) NOT NULL,
  `EMP_FLAGS04` char(2) NOT NULL,
  `EMP_FLAGS05` char(2) NOT NULL,
  `EMP_FLAGS06` char(2) NOT NULL,
  `EMP_FLAGS07` char(2) NOT NULL,
  `EMP_FLAGS08` char(2) NOT NULL,
  `EMP_FLAGS09` char(2) NOT NULL,
  `EMP_FLAGS10` char(2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `EMP_NUMBER` (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_EMPLOYEE_AUX`
--

DROP TABLE IF EXISTS `HISTORY_EMPLOYEE_AUX`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_EMPLOYEE_AUX` (
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `EMP_NO_ROUTING_1` decimal(9,0) NOT NULL,
  `EMP_NO_ROUTING_2` decimal(9,0) NOT NULL,
  `EMP_NO_ACCOUNT_1` char(20) NOT NULL,
  `EMP_NO_ACCOUNT_2` char(20) NOT NULL,
  `EMP_TY_ACCOUNT_1` char(10) NOT NULL,
  `EMP_TY_ACCOUNT_2` char(10) NOT NULL,
  `EMP_FLAGS01` char(2) NOT NULL,
  `EMP_FLAGS02` char(2) NOT NULL,
  `EMP_FLAGS03` char(2) NOT NULL,
  `EMP_FLAGS04` char(2) NOT NULL,
  `EMP_FLAGS05` char(2) NOT NULL,
  `EMP_FLAGS06` char(2) NOT NULL,
  `EMP_FLAGS07` char(2) NOT NULL,
  `EMP_FLAGS08` char(2) NOT NULL,
  `EMP_FLAGS09` char(2) NOT NULL,
  `EMP_FLAGS10` char(2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `EMP_NUMBER` (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_EMPLOYEE_DEDUCTIONS`
--

DROP TABLE IF EXISTS `HISTORY_EMPLOYEE_DEDUCTIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_EMPLOYEE_DEDUCTIONS` (
  `EMP_NUMBER` decimal(6,0) NOT NULL DEFAULT '0',
  `EMP_DED_KEY01` char(2) NOT NULL,
  `EMP_DED_KEY02` char(2) NOT NULL,
  `EMP_DED_KEY03` char(2) NOT NULL,
  `EMP_DED_KEY04` char(2) NOT NULL,
  `EMP_DED_KEY05` char(2) NOT NULL,
  `EMP_DED_KEY06` char(2) NOT NULL,
  `EMP_DED_KEY07` char(2) NOT NULL,
  `EMP_DED_KEY08` char(2) NOT NULL,
  `EMP_DED_KEY09` char(2) NOT NULL,
  `EMP_DED_KEY10` char(2) NOT NULL,
  `EMP_DED_KEY11` char(2) NOT NULL,
  `EMP_DED_KEY12` char(2) NOT NULL,
  `EMP_DED_KEY13` char(2) NOT NULL,
  `EMP_DED_KEY14` char(2) NOT NULL,
  `EMP_DED_KEY15` char(2) NOT NULL,
  `EMP_DED_KEY16` char(2) NOT NULL,
  `EMP_DED_AMOUNT01` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT02` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT03` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT04` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT05` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT06` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT07` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT08` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT09` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT10` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT11` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT12` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT13` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT14` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT15` decimal(9,4) NOT NULL,
  `EMP_DED_AMOUNT16` decimal(9,4) NOT NULL,
  `EMP_BAL_AMOUNT01` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT02` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT03` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT04` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT05` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT06` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT07` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT08` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT09` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT10` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT11` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT12` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT13` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT14` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT15` decimal(9,2) NOT NULL,
  `EMP_BAL_AMOUNT16` decimal(9,2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `EMP_NUMBER` (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_MISC`
--

DROP TABLE IF EXISTS `HISTORY_MISC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_MISC` (
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `MISC_POSITION01` char(2) NOT NULL,
  `MISC_POSITION02` char(2) NOT NULL,
  `MISC_POSITION03` char(2) NOT NULL,
  `MISC_POSITION04` char(2) NOT NULL,
  `MISC_POSITION05` char(2) NOT NULL,
  `MISC_POSITION06` char(2) NOT NULL,
  `MISC_POSITION07` char(2) NOT NULL,
  `MISC_POSITION08` char(2) NOT NULL,
  `MISC_POSITION09` char(2) NOT NULL,
  `MISC_POSITION10` char(2) NOT NULL,
  `MISC_DIGIT01` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT02` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT03` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT04` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT05` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT06` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT07` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT08` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT09` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT10` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_NUMERIC01` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC02` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC03` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC04` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC05` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC06` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC07` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC08` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC09` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC10` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC11` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC12` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC13` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC14` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC15` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC16` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC17` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC18` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC19` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC20` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_DD_NUMBER` char(10) NOT NULL,
  `MISC_ALPHA01` char(10) NOT NULL,
  `MISC_ALPHA02` char(10) NOT NULL,
  `MISC_ALPHA03` char(10) NOT NULL,
  `MISC_ALPHA04` char(10) NOT NULL,
  `MISC_DESCRIPTION01` char(30) NOT NULL,
  `MISC_DESCRIPTION02` char(30) NOT NULL,
  `MISC_DESCRIPTION03` char(30) NOT NULL,
  `MISC_DESCRIPTION04` char(30) NOT NULL,
  `MISC_DESCRIPTION05` char(30) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  KEY `EMP_NUMBER` (`EMP_NUMBER`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_OPTIONS`
--

DROP TABLE IF EXISTS `HISTORY_OPTIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_OPTIONS` (
  `NM_PROGRAM` char(8) NOT NULL,
  `FG_OPTION_1` char(50) NOT NULL,
  `FG_OPTION_2` char(50) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` char(8) NOT NULL,
  `TM_ENTERED` char(6) NOT NULL,
  `NM_USER` char(8) NOT NULL,
  KEY `NM_PROGRAM` (`NM_PROGRAM`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Program options history';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HISTORY_STATE_WITHHOLDING`
--

DROP TABLE IF EXISTS `HISTORY_STATE_WITHHOLDING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HISTORY_STATE_WITHHOLDING` (
  `CD_STATE` decimal(2,0) NOT NULL,
  `AM_SINGLE_BASE_1` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_2` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_3` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_4` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_5` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_6` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_7` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_8` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_9` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_1` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_2` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_3` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_4` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_5` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_6` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_7` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_8` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_9` decimal(9,2) NOT NULL,
  `PCT_SINGLE_1` decimal(8,6) NOT NULL,
  `PCT_SINGLE_2` decimal(8,6) NOT NULL,
  `PCT_SINGLE_3` decimal(8,6) NOT NULL,
  `PCT_SINGLE_4` decimal(8,6) NOT NULL,
  `PCT_SINGLE_5` decimal(8,6) NOT NULL,
  `PCT_SINGLE_6` decimal(8,6) NOT NULL,
  `PCT_SINGLE_7` decimal(8,6) NOT NULL,
  `PCT_SINGLE_8` decimal(8,6) NOT NULL,
  `PCT_SINGLE_9` decimal(8,6) NOT NULL,
  `AM_MARRIED_BASE_1` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_2` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_3` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_4` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_5` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_6` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_7` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_8` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_9` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_1` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_2` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_3` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_4` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_5` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_6` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_7` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_8` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_9` decimal(9,2) NOT NULL,
  `PCT_MARRIED_1` decimal(8,6) NOT NULL,
  `PCT_MARRIED_2` decimal(8,6) NOT NULL,
  `PCT_MARRIED_3` decimal(8,6) NOT NULL,
  `PCT_MARRIED_4` decimal(8,6) NOT NULL,
  `PCT_MARRIED_5` decimal(8,6) NOT NULL,
  `PCT_MARRIED_6` decimal(8,6) NOT NULL,
  `PCT_MARRIED_7` decimal(8,6) NOT NULL,
  `PCT_MARRIED_8` decimal(8,6) NOT NULL,
  `PCT_MARRIED_9` decimal(8,6) NOT NULL,
  `AM_HEAD_BASE_1` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_2` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_3` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_4` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_5` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_6` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_7` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_8` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_9` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_1` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_2` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_3` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_4` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_5` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_6` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_7` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_8` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_9` decimal(9,2) NOT NULL,
  `PCT_HEAD_1` decimal(8,6) NOT NULL,
  `PCT_HEAD_2` decimal(8,6) NOT NULL,
  `PCT_HEAD_3` decimal(8,6) NOT NULL,
  `PCT_HEAD_4` decimal(8,6) NOT NULL,
  `PCT_HEAD_5` decimal(8,6) NOT NULL,
  `PCT_HEAD_6` decimal(8,6) NOT NULL,
  `PCT_HEAD_7` decimal(8,6) NOT NULL,
  `PCT_HEAD_8` decimal(8,6) NOT NULL,
  `PCT_HEAD_9` decimal(8,6) NOT NULL,
  `AM_SUTA_MAX` decimal(9,2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(8) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HOURS`
--

DROP TABLE IF EXISTS `HOURS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `HOURS` (
  `PRIMARY_KEY` int NOT NULL AUTO_INCREMENT,
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `H_HOURS_REG` decimal(6,2) NOT NULL,
  `H_HOURS_OT` decimal(6,2) NOT NULL,
  `H_HOURS_PAYA` decimal(6,2) NOT NULL,
  `H_HOURS_PAYB` decimal(6,2) NOT NULL,
  `H_HOURS_PAYC` decimal(6,2) NOT NULL,
  `H_HOURS_PAYD` decimal(6,2) NOT NULL,
  `H_HOURS_PAYE` decimal(6,2) NOT NULL,
  `H_HOURS_PAYF` decimal(6,2) NOT NULL,
  `H_HOURS_PAYG` decimal(6,2) NOT NULL,
  `H_HOURS_PAYH` decimal(6,2) NOT NULL,
  `H_HOURS_PAYI` decimal(6,2) NOT NULL,
  `H_HOURS_PAYJ` decimal(6,2) NOT NULL,
  `H_HOURS_PAYK` decimal(6,2) NOT NULL,
  `H_HOURS_PAYL` decimal(6,2) NOT NULL,
  `H_HOURS_PAYM` decimal(6,2) NOT NULL,
  `H_HOURS_PAYN` decimal(6,2) NOT NULL,
  `H_AMOUNT_REG` decimal(9,2) NOT NULL,
  `H_AMOUNT_OT` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYA` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYB` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYC` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYD` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYE` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYF` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYG` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYH` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYI` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYJ` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYK` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYL` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYM` decimal(9,2) NOT NULL,
  `H_AMOUNT_PAYN` decimal(9,2) NOT NULL,
  `H_RATE_REG` decimal(9,4) NOT NULL,
  `H_RATE_OT` decimal(9,4) NOT NULL,
  `H_RATE_PAYA` decimal(9,4) NOT NULL,
  `H_RATE_PAYB` decimal(9,4) NOT NULL,
  `H_RATE_PAYC` decimal(9,4) NOT NULL,
  `H_RATE_PAYD` decimal(9,4) NOT NULL,
  `H_RATE_PAYE` decimal(9,4) NOT NULL,
  `H_RATE_PAYF` decimal(9,4) NOT NULL,
  `H_RATE_PAYG` decimal(9,4) NOT NULL,
  `H_RATE_PAYH` decimal(9,4) NOT NULL,
  `H_RATE_PAYI` decimal(9,4) NOT NULL,
  `H_RATE_PAYJ` decimal(9,4) NOT NULL,
  `H_RATE_PAYK` decimal(9,4) NOT NULL,
  `H_RATE_PAYL` decimal(9,4) NOT NULL,
  `H_RATE_PAYM` decimal(9,4) NOT NULL,
  `H_RATE_PAYN` decimal(9,4) NOT NULL,
  `H_FED_FLAG` char(2) NOT NULL,
  `H_FED_AMT` decimal(9,4) NOT NULL,
  `H_ST_FLAG` char(2) NOT NULL,
  `H_ST_AMT` decimal(9,4) NOT NULL,
  `H_CHECK_NUMBER` decimal(6,0) NOT NULL,
  `H_RATE` decimal(9,4) NOT NULL,
  `H_LABOR` decimal(9,0) NOT NULL,
  PRIMARY KEY (`PRIMARY_KEY`),
  KEY `EMP_NUMBER` (`EMP_NUMBER`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Employee Hours';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MISC`
--

DROP TABLE IF EXISTS `MISC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MISC` (
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `MISC_POSITION01` char(2) NOT NULL,
  `MISC_POSITION02` char(2) NOT NULL,
  `MISC_POSITION03` char(2) NOT NULL,
  `MISC_POSITION04` char(2) NOT NULL,
  `MISC_POSITION05` char(2) NOT NULL,
  `MISC_POSITION06` char(2) NOT NULL,
  `MISC_POSITION07` char(2) NOT NULL,
  `MISC_POSITION08` char(2) NOT NULL,
  `MISC_POSITION09` char(2) NOT NULL,
  `MISC_POSITION10` char(2) NOT NULL,
  `MISC_DIGIT01` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT02` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT03` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT04` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT05` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT06` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT07` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT08` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT09` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_DIGIT10` decimal(5,0) NOT NULL DEFAULT '0',
  `MISC_NUMERIC01` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC02` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC03` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC04` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC05` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC06` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC07` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC08` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC09` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC10` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC11` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC12` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC13` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC14` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC15` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC16` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC17` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC18` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC19` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_NUMERIC20` decimal(10,2) NOT NULL DEFAULT '0.00',
  `MISC_DD_NUMBER` char(10) NOT NULL,
  `MISC_ALPHA01` char(10) NOT NULL,
  `MISC_ALPHA02` char(10) NOT NULL,
  `MISC_ALPHA03` char(10) NOT NULL,
  `MISC_ALPHA04` char(10) NOT NULL,
  `MISC_DESCRIPTION01` char(30) NOT NULL,
  `MISC_DESCRIPTION02` char(30) NOT NULL,
  `MISC_DESCRIPTION03` char(30) NOT NULL,
  `MISC_DESCRIPTION04` char(30) NOT NULL,
  `MISC_DESCRIPTION05` char(30) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(10) NOT NULL,
  PRIMARY KEY (`EMP_NUMBER`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Employee Miscellaneous Info';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `OPTIONS`
--

DROP TABLE IF EXISTS `OPTIONS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `OPTIONS` (
  `NM_PROGRAM` char(8) NOT NULL,
  `FG_OPTION_1` char(50) NOT NULL,
  `FG_OPTION_2` char(50) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` char(8) NOT NULL,
  `TM_ENTERED` char(6) NOT NULL,
  `NM_USER` char(8) NOT NULL,
  PRIMARY KEY (`NM_PROGRAM`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Program options';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `QUARTER`
--

DROP TABLE IF EXISTS `QUARTER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `QUARTER` (
  `EMP_NUMBER` decimal(6,0) NOT NULL,
  `QUARTER_QUARTER` decimal(2,0) NOT NULL,
  `QTR_HOURS_REG` decimal(6,2) NOT NULL,
  `QTR_HOURS_OT` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYA` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYB` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYC` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYD` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYE` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYF` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYG` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYH` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYI` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYJ` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYK` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYL` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYM` decimal(6,2) NOT NULL,
  `QTR_HOURS_PAYN` decimal(6,2) NOT NULL,
  `QTR_AMOUNT_REG` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_OT` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYA` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYB` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYC` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYD` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYE` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYF` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYG` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYH` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYI` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYJ` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYK` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYL` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYM` decimal(9,2) NOT NULL,
  `QTR_AMOUNT_PAYN` decimal(9,2) NOT NULL,
  `QTR_GROSS` decimal(9,2) NOT NULL,
  `QTR_FWH` decimal(9,2) NOT NULL,
  `QTR_FICA` decimal(9,2) NOT NULL,
  `QTR_MCARE` decimal(9,2) NOT NULL,
  `QTR_STATE` decimal(9,2) NOT NULL,
  `QTR_SDI` decimal(9,2) NOT NULL,
  `QTR_EIC` decimal(9,2) NOT NULL,
  `QTR_LOCAL` decimal(9,2) NOT NULL,
  `QTR_DED01` decimal(9,2) NOT NULL,
  `QTR_DED02` decimal(9,2) NOT NULL,
  `QTR_DED03` decimal(9,2) NOT NULL,
  `QTR_DED04` decimal(9,2) NOT NULL,
  `QTR_DED05` decimal(9,2) NOT NULL,
  `QTR_DED06` decimal(9,2) NOT NULL,
  `QTR_DED07` decimal(9,2) NOT NULL,
  `QTR_DED08` decimal(9,2) NOT NULL,
  `QTR_DED09` decimal(9,2) NOT NULL,
  `QTR_DED10` decimal(9,2) NOT NULL,
  `QTR_DED11` decimal(9,2) NOT NULL,
  `QTR_DED12` decimal(9,2) NOT NULL,
  `QTR_DED13` decimal(9,2) NOT NULL,
  `QTR_DED14` decimal(9,2) NOT NULL,
  `QTR_DED15` decimal(9,2) NOT NULL,
  `QTR_DED16` decimal(9,2) NOT NULL,
  `QTR_NET` decimal(9,2) NOT NULL,
  KEY `QUARTER_QUARTER` (`QUARTER_QUARTER`),
  KEY `EMP_NUMBER` (`EMP_NUMBER`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COMMENT='Quarter Summaries';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `STATE_WITHHOLDING`
--

DROP TABLE IF EXISTS `STATE_WITHHOLDING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `STATE_WITHHOLDING` (
  `CD_STATE` decimal(2,0) NOT NULL,
  `AM_SINGLE_BASE_1` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_2` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_3` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_4` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_5` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_6` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_7` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_8` decimal(9,2) NOT NULL,
  `AM_SINGLE_BASE_9` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_1` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_2` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_3` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_4` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_5` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_6` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_7` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_8` decimal(9,2) NOT NULL,
  `AM_SINGLE_OVER_9` decimal(9,2) NOT NULL,
  `PCT_SINGLE_1` decimal(8,6) NOT NULL,
  `PCT_SINGLE_2` decimal(8,6) NOT NULL,
  `PCT_SINGLE_3` decimal(8,6) NOT NULL,
  `PCT_SINGLE_4` decimal(8,6) NOT NULL,
  `PCT_SINGLE_5` decimal(8,6) NOT NULL,
  `PCT_SINGLE_6` decimal(8,6) NOT NULL,
  `PCT_SINGLE_7` decimal(8,6) NOT NULL,
  `PCT_SINGLE_8` decimal(8,6) NOT NULL,
  `PCT_SINGLE_9` decimal(8,6) NOT NULL,
  `AM_MARRIED_BASE_1` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_2` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_3` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_4` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_5` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_6` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_7` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_8` decimal(9,2) NOT NULL,
  `AM_MARRIED_BASE_9` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_1` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_2` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_3` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_4` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_5` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_6` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_7` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_8` decimal(9,2) NOT NULL,
  `AM_MARRIED_OVER_9` decimal(9,2) NOT NULL,
  `PCT_MARRIED_1` decimal(8,6) NOT NULL,
  `PCT_MARRIED_2` decimal(8,6) NOT NULL,
  `PCT_MARRIED_3` decimal(8,6) NOT NULL,
  `PCT_MARRIED_4` decimal(8,6) NOT NULL,
  `PCT_MARRIED_5` decimal(8,6) NOT NULL,
  `PCT_MARRIED_6` decimal(8,6) NOT NULL,
  `PCT_MARRIED_7` decimal(8,6) NOT NULL,
  `PCT_MARRIED_8` decimal(8,6) NOT NULL,
  `PCT_MARRIED_9` decimal(8,6) NOT NULL,
  `AM_HEAD_BASE_1` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_2` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_3` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_4` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_5` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_6` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_7` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_8` decimal(9,2) NOT NULL,
  `AM_HEAD_BASE_9` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_1` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_2` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_3` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_4` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_5` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_6` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_7` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_8` decimal(9,2) NOT NULL,
  `AM_HEAD_OVER_9` decimal(9,2) NOT NULL,
  `PCT_HEAD_1` decimal(8,6) NOT NULL,
  `PCT_HEAD_2` decimal(8,6) NOT NULL,
  `PCT_HEAD_3` decimal(8,6) NOT NULL,
  `PCT_HEAD_4` decimal(8,6) NOT NULL,
  `PCT_HEAD_5` decimal(8,6) NOT NULL,
  `PCT_HEAD_6` decimal(8,6) NOT NULL,
  `PCT_HEAD_7` decimal(8,6) NOT NULL,
  `PCT_HEAD_8` decimal(8,6) NOT NULL,
  `PCT_HEAD_9` decimal(8,6) NOT NULL,
  `AM_SUTA_MAX` decimal(9,2) NOT NULL,
  `NO_VERSION` decimal(9,0) NOT NULL,
  `DT_ENTERED` date NOT NULL,
  `TM_ENTERED` time NOT NULL,
  `NM_USER` char(8) NOT NULL,
  PRIMARY KEY (`CD_STATE`) USING BTREE
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-01 11:08:29
